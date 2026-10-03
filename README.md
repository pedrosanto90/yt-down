# youtdown

Download YouTube audio as MP3 through a simple web page, the CLI or the API.

For local execution, requires [uv](https://docs.astral.sh/uv/) and `ffmpeg`
(used to extract the audio track). Docker includes these dependencies.

## Docker Compose

With Docker and the Compose plugin installed, run:

```sh
docker compose up --build -d
```

Open http://127.0.0.1:8001. The container includes Python and `ffmpeg`, runs
as a non-root user, and checks `/health` automatically. Dependencies are
installed from `uv.lock` using the [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).

The port is available on the local computer only. If port 8001 is already
in use, choose another host port:

```sh
PORT=8002 docker compose up --build -d
```

In that case, open http://127.0.0.1:8002.

```sh
docker compose logs -f
docker compose ps
docker compose down
```

MP3 files are stored in a Docker named volume, separate from the local
`downloads/` directory, and survive container recreation and `docker compose down`.
`docker compose down -v` also deletes the stored MP3 files. Job history is
kept in memory and resets when the container restarts; run a single worker.
After code changes, run `docker compose up --build -d` again.

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
uv run youtdown-web --reload
```

The web service uses port **8001**. You can also start it with `make dev`
(with reload), `make run` (without reload), or `uv run python -m youtdown`.
All these commands use the same server configuration.

If invoking Uvicorn directly, specify the service's port explicitly:

```sh
uv run uvicorn youtdown.web:app --reload --port 8001
```

The bare Uvicorn command does not read the project's server configuration;
always include `--port 8001` when using it directly.

Open http://127.0.0.1:8001 to use the web page. Paste a YouTube link and click
**Descarregar MP3**. The page waits for the MP3 to be ready and starts the
browser download automatically, with a **Guardar MP3** link to retry saving.
The browser's settings determine whether it asks for a save location or saves
directly to its downloads folder. Keep the page open while the audio is prepared.

HTML, CSS and JavaScript are served by FastAPI; no frontend build is needed.
`ffmpeg` must be installed to convert the audio into MP3 (192 kbps).
MP3 files are also kept on the server under `downloads/<job_id>/`.

Interactive API docs are available at http://127.0.0.1:8001/docs.

### Endpoints

| Method | Path                 | Description                                  |
| ------ | -------------------- | -------------------------------------------- |
| `GET`  | `/`                  | Web page                                     |
| `POST` | `/downloads`         | Queue a download (`{"url": "..."}`), returns `202` with a `job_id`. Only MP3 audio is supported. |
| `GET`  | `/downloads`         | List all jobs                                |
| `GET`  | `/downloads/{job_id}`| Get a job's status (`queued`/`running`/`done`/`failed`) |
| `GET`  | `/files/{filename}`  | Download a finished MP3 (use the job's `filename`, including any subdirectory) |
| `GET`  | `/health`            | Health check                                 |

### Example

```sh
curl -X POST http://127.0.0.1:8001/downloads \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

curl http://127.0.0.1:8001/downloads/<job_id>

curl -O http://127.0.0.1:8001/files/<filename>
```

Downloads run in the background; poll the job status until it is `done`, then
fetch the file. Jobs are kept in memory only.

## Tests

```sh
uv run --with httpx python -m unittest discover -s tests -v
```

Tests use simulated downloads and do not contact YouTube.
