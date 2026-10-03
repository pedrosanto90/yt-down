import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from youtdown.downloader import DEFAULT_DOWNLOAD_DIR, download_audio

DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR.resolve()
STATIC_DIR = Path(__file__).parent / "static"

JobStatus = Literal["queued", "running", "done", "failed"]


@dataclass
class Job:
    id: str
    url: str
    created_at: datetime
    format: Literal["audio"] = "audio"
    status: JobStatus = "queued"
    filename: str | None = None
    error: str | None = None


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def _create_job(url: str, format: Literal["audio"] = "audio") -> Job:
    job = Job(id=str(uuid.uuid4()), url=url, created_at=datetime.now(timezone.utc), format=format)
    with _lock:
        _jobs[job.id] = job
    return job


def _get_job(job_id: str) -> Job:
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


def _update_job(job_id: str, **changes: object) -> None:
    with _lock:
        job = _jobs[job_id]
        for key, value in changes.items():
            setattr(job, key, value)


def _run_download(job_id: str, url: str, format: Literal["audio"] = "audio") -> None:
    _update_job(job_id, status="running")
    try:
        path = download_audio(url, DOWNLOAD_DIR / job_id)
    except Exception as error:  # noqa: BLE001 - report any download failure to the client
        _update_job(job_id, status="failed", error=str(error))
    else:
        _update_job(job_id, status="done", filename=str(path.relative_to(DOWNLOAD_DIR)))


class DownloadRequest(BaseModel):
    url: str
    format: Literal["audio"] = "audio"

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https") or not (
            host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com")
        ) or parsed.username or parsed.password:
            raise ValueError("Introduz um link válido do YouTube.")
        return value


class JobResponse(BaseModel):
    job_id: str
    url: str
    status: JobStatus
    filename: str | None = None
    error: str | None = None


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        url=job.url,
        status=job.status,
        filename=job.filename,
        error=job.error,
    )


app = FastAPI(title="youtdown", description="Download YouTube audio as MP3.")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/downloads", response_model=JobResponse, status_code=202)
def create_download(request: DownloadRequest, background: BackgroundTasks) -> JobResponse:
    job = _create_job(request.url, request.format)
    background.add_task(_run_download, job.id, job.url, job.format)
    return _to_response(job)


@app.get("/downloads", response_model=list[JobResponse])
def list_downloads() -> list[JobResponse]:
    with _lock:
        jobs = list(_jobs.values())
    return [_to_response(job) for job in jobs]


@app.get("/downloads/{job_id}", response_model=JobResponse)
def get_download(job_id: str) -> JobResponse:
    return _to_response(_get_job(job_id))


@app.get("/files/{filename:path}")
def get_file(filename: str) -> FileResponse:
    path = (DOWNLOAD_DIR / filename).resolve()
    if not path.is_relative_to(DOWNLOAD_DIR):
        raise HTTPException(status_code=400, detail="invalid filename")
    if path.suffix.lower() != ".mp3" or not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, media_type="audio/mpeg", filename=path.name)
