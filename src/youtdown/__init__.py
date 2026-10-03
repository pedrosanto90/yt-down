import sys

import yt_dlp

from youtdown.downloader import download_audio


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: youtdown <youtube-url>")
        sys.exit(1)

    url = sys.argv[1]

    print("Youtube Audio Downloader")

    try:
        path = download_audio(url)
    except yt_dlp.utils.DownloadError as error:
        print(f"Download failed: {error}")
        sys.exit(1)

    print(f"Saved to {path}")
