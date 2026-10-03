# youtdown

Download YouTube audio as MP3 from the command line or as a web service.

Requires [uv](https://docs.astral.sh/uv/) and `ffmpeg` (used to extract the
audio track).

## Install

```sh
uv sync
```

## CLI usage

```sh
uv run youtdown <youtube-url>
```

Downloaded files are written to the `downloads/` directory as MP3 (192 kbps).

Example:

```sh
uv run youtdown https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Web service

Start the FastAPI server:

```sh
uv run uvicorn youtdown.web:app --reload
```

Interactive API docs are available at http://127.0.0.1:8000/docs.

### Endpoints

| Method | Path                 | Description                                  |
| ------ | -------------------- | -------------------------------------------- |
| `POST` | `/downloads`         | Queue a download (`{"url": "..."}`), returns `202` with a `job_id` |
| `GET`  | `/downloads`         | List all jobs                                |
| `GET`  | `/downloads/{job_id}`| Get a job's status (`queued`/`running`/`done`/`failed`) |
| `GET`  | `/files/{filename}`  | Download a finished MP3                       |
| `GET`  | `/health`            | Health check                                 |

### Example

```sh
curl -X POST http://127.0.0.1:8000/downloads \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

curl http://127.0.0.1:8000/downloads/<job_id>

curl -O http://127.0.0.1:8000/files/<filename>
```

Downloads run in the background; poll the job status until it is `done`, then
fetch the file. Jobs are kept in memory only.
