from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError

DEFAULT_DOWNLOAD_DIR = Path("downloads")


def download_audio(url: str, download_dir: Path = DEFAULT_DOWNLOAD_DIR) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    def record_path(filename: str) -> None:
        paths.append(Path(filename))

    with yt_dlp.YoutubeDL({
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": str(download_dir / "%(title).180B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "post_hooks": [record_path],
    }) as ydl:
        _ = ydl.extract_info(url, download=True)

    if not paths or not paths[-1].is_file():
        raise DownloadError("could not determine output file path")

    return paths[-1]
