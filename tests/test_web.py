import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from youtdown import web
from youtdown.downloader import download_audio


class WebTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        patcher = patch.object(web, "DOWNLOAD_DIR", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        web._jobs.clear()
        self.client = TestClient(web.app)

    def test_page_and_assets(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="download-form"', response.text)
        for asset in ("app.js", "style.css"):
            self.assertEqual(self.client.get(f"/static/{asset}").status_code, 200)

    def test_audio_job_and_file_delivery(self):
        def fake_download(url, directory):
            directory.mkdir()
            path = directory / "Áudio de teste [abc].mp3"
            path.write_bytes(b"audio-content")
            return path

        with patch.object(web, "download_audio", side_effect=fake_download):
            response = self.client.post("/downloads", json={
                "url": "https://youtu.be/abc", "format": "audio",
            })
        self.assertEqual(response.status_code, 202)
        job = self.client.get(f"/downloads/{response.json()['job_id']}").json()
        self.assertEqual(job["status"], "done")
        response = self.client.get(f"/files/{job['filename']}")
        self.assertEqual(response.content, b"audio-content")
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertIn("attachment;", response.headers["content-disposition"])

    def test_audio_remains_default(self):
        path = self.root / "audio.mp3"
        path.write_bytes(b"audio-content")
        with patch.object(web, "download_audio", return_value=path) as download:
            response = self.client.post("/downloads", json={"url": "https://youtu.be/abc"})
        download.assert_called_once_with("https://youtu.be/abc", self.root / response.json()["job_id"])
        job = self.client.get(f"/downloads/{response.json()['job_id']}").json()
        self.assertEqual(job["filename"], "audio.mp3")
        self.assertEqual(self.client.get("/files/audio.mp3").headers["content-type"], "audio/mpeg")

    def test_download_failure(self):
        with patch.object(web, "download_audio", side_effect=RuntimeError("Audio unavailable")):
            response = self.client.post("/downloads", json={
                "url": "https://youtu.be/abc", "format": "audio",
            })
        job = self.client.get(f"/downloads/{response.json()['job_id']}").json()
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["error"], "Audio unavailable")

    def test_video_format_is_rejected(self):
        response = self.client.post("/downloads", json={
            "url": "https://youtu.be/abc", "format": "video",
        })
        self.assertEqual(response.status_code, 422)
        path = self.root / "old-video.mp4"
        path.write_bytes(b"old-video")
        self.assertEqual(self.client.get("/files/old-video.mp4").status_code, 404)

    def test_validation_and_missing_files(self):
        for url in ("https://example.com/video", "https://youtube.com.evil.test/video", "invalid"):
            self.assertEqual(self.client.post("/downloads", json={"url": url}).status_code, 422)
        self.assertEqual(self.client.get("/files/missing.mp3").status_code, 404)
        self.assertEqual(self.client.get("/files/%2e%2e/outside.mp3").status_code, 400)
        self.assertEqual(self.client.get("/downloads/missing").status_code, 404)

    def test_downloader_uses_final_converted_path(self):
        final = self.root / "converted.mp3"
        final.write_bytes(b"merged")
        with patch("youtdown.downloader.yt_dlp.YoutubeDL") as factory:
            def extract(*args, **kwargs):
                factory.call_args.args[0]["post_hooks"][0](str(final))
            factory.return_value.__enter__.return_value.extract_info.side_effect = extract
            self.assertEqual(download_audio("https://youtu.be/abc", self.root), final)
        self.assertTrue(factory.call_args.args[0]["noplaylist"])
        self.assertEqual(factory.call_args.args[0]["postprocessors"][0]["preferredcodec"], "mp3")


if __name__ == "__main__":
    unittest.main()
