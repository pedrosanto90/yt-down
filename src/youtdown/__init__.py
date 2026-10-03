import sys

import yt_dlp


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: youtdown <youtube-url>")
        sys.exit(1)

    url = sys.argv[1]

    print("Youtube Audio Downloader")

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": "downloads/%(title)s.%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as error:
        print(f"Download failed: {error}")
        sys.exit(1)
