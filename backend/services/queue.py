"""In-process job queue with cancel-latest semantics. Swap for Celery+Redis later."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

from config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    cancel_event: threading.Event = field(default_factory=threading.Event)


class GenerationQueue:
    def __init__(self, worker_fn: Callable[[Job, Dict[str, Any]], Dict[str, Any]]) -> None:
        self._worker_fn = worker_fn
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pending: list[tuple[str, Dict[str, Any]]] = []
        self._active_job_id: Optional[str] = None
        self._worker = threading.Thread(target=self._run, daemon=True, name="gen-worker")
        self._worker.start()

    def submit(self, payload: Dict[str, Any]) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(id=job_id)

        with self._lock:
            # Drop stale queued jobs when user keeps drawing (cancel-latest)
            for queued_id, _ in list(self._pending):
                old = self._jobs.get(queued_id)
                if old and old.status == JobStatus.QUEUED:
                    old.status = JobStatus.CANCELLED
                    old.cancel_event.set()

            if self._active_job_id:
                active = self._jobs.get(self._active_job_id)
                if active and active.status == JobStatus.RUNNING:
                    active.cancel_event.set()

            while len(self._pending) >= settings.max_queue_size:
                dropped_id, _ = self._pending.pop(0)
                dropped = self._jobs.get(dropped_id)
                if dropped:
                    dropped.status = JobStatus.CANCELLED
                    dropped.cancel_event.set()

            self._jobs[job_id] = job
            self._pending.append((job_id, payload))

        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def _run(self) -> None:
        while True:
            job_id: Optional[str] = None
            payload: Dict[str, Any] = {}

            with self._lock:
                if self._pending:
                    job_id, payload = self._pending.pop(0)

            if not job_id:
                time.sleep(0.05)
                continue

            job = self._jobs.get(job_id)
            if not job or job.status == JobStatus.CANCELLED:
                continue

            job.status = JobStatus.RUNNING
            self._active_job_id = job_id

            try:
                if job.cancel_event.is_set():
                    job.status = JobStatus.CANCELLED
                    continue

                result = self._worker_fn(job, payload)

                if job.cancel_event.is_set():
                    job.status = JobStatus.CANCELLED
                else:
                    job.result = result
                    job.status = JobStatus.COMPLETED
            except Exception as exc:
                logger.exception("Job %s failed", job_id)
                job.error = str(exc)
                job.status = JobStatus.FAILED
            finally:
                if self._active_job_id == job_id:
                    self._active_job_id = None
