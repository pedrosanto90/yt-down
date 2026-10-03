# youtdown

Download YouTube audio as MP3 from the command line.

Requires [uv](https://docs.astral.sh/uv/) and `ffmpeg` (used to extract the
audio track).

## Install

```sh
uv sync
```

## Usage

```sh
uv run youtdown <youtube-url>
```

Downloaded files are written to the `downloads/` directory as MP3 (192 kbps).

Example:

```sh
uv run youtdown https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
