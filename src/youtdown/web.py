import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

from youtdown.downloader import DEFAULT_DOWNLOAD_DIR, download_audio

DOWNLOAD_DIR = DEFAULT_DOWNLOAD_DIR.resolve()

JobStatus = Literal["queued", "running", "done", "failed"]


@dataclass
class Job:
    id: str
    url: str
    created_at: datetime
    status: JobStatus = "queued"
    filename: str | None = None
    error: str | None = None


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def _create_job(url: str) -> Job:
    job = Job(id=str(uuid.uuid4()), url=url, created_at=datetime.now(timezone.utc))
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


def _run_download(job_id: str, url: str) -> None:
    _update_job(job_id, status="running")
    try:
        path = download_audio(url, DOWNLOAD_DIR)
    except Exception as error:  # noqa: BLE001 - report any download failure to the client
        _update_job(job_id, status="failed", error=str(error))
    else:
        _update_job(job_id, status="done", filename=path.name)


class DownloadRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
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


app = FastAPI(title="youtdown", description="Download YouTube audio as MP3 over HTTP.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/downloads", response_model=JobResponse, status_code=202)
def create_download(request: DownloadRequest, background: BackgroundTasks) -> JobResponse:
    job = _create_job(request.url)
    background.add_task(_run_download, job.id, job.url)
    return _to_response(job)


@app.get("/downloads", response_model=list[JobResponse])
def list_downloads() -> list[JobResponse]:
    with _lock:
        jobs = list(_jobs.values())
    return [_to_response(job) for job in jobs]


@app.get("/downloads/{job_id}", response_model=JobResponse)
def get_download(job_id: str) -> JobResponse:
    return _to_response(_get_job(job_id))


@app.get("/files/{filename}")
def get_file(filename: str) -> FileResponse:
    path = (DOWNLOAD_DIR / filename).resolve()
    if path.parent != DOWNLOAD_DIR:
        raise HTTPException(status_code=400, detail="invalid filename")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, media_type="audio/mpeg", filename=path.name)
