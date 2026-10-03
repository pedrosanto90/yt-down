from pathlib import Path

import yt_dlp

DEFAULT_DOWNLOAD_DIR = Path("downloads")


def download_audio(url: str, download_dir: Path = DEFAULT_DOWNLOAD_DIR) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": str(download_dir / "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    requested = info.get("requested_downloads") or [info]
    filepath = requested[0].get("filepath")

    if not filepath:
        raise yt_dlp.utils.DownloadError("could not determine output file path")

    return Path(filepath)
