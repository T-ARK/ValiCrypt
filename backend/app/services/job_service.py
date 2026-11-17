"""Asynchronous Job Processing Service.

Manages background encoding, decoding, and verification tasks.
Provides thread-safe state updates, progress tracking, and file lifecycle management.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Callable, Dict, Optional
import uuid
from app.core.config import settings
from app.core.logging import logger
from app.db.models import JobOperation, JobRecord, JobRepository, JobStatus

_executor = ThreadPoolExecutor(max_workers=4)


def get_output_dir() -> Path:
    output_dir = settings.TEMP_DIRECTORY / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class JobService:
    @staticmethod
    def create_job(
        operation: JobOperation,
        carrier_type: str,
        carrier_size: int,
        payload_type: Optional[str] = None,
        payload_size: Optional[int] = None,
    ) -> JobRecord:
        job_id = str(uuid.uuid4())
        record = JobRecord(
            id=job_id,
            status=JobStatus.QUEUED,
            operation=operation,
            carrier_type=carrier_type,
            payload_type=payload_type,
            carrier_size=carrier_size,
            payload_size=payload_size,
            progress=0,
        )
        return JobRepository.create(record)

    @staticmethod
    def get_job(job_id: str) -> Optional[JobRecord]:
        return JobRepository.get(job_id)

    @staticmethod
    def list_jobs(limit: int = 50) -> list[JobRecord]:
        return JobRepository.list_recent(limit)

    @staticmethod
    def update_progress(job_id: str, status: JobStatus, progress: int) -> None:
        JobRepository.update_status(job_id, status=status, progress=progress)

    @staticmethod
    def mark_completed(
        job_id: str,
        output_file_id: Optional[str] = None,
        output_filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        JobRepository.update_status(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            output_file_id=output_file_id,
            output_filename=output_filename,
            mime_type=mime_type,
        )

    @staticmethod
    def mark_failed(job_id: str, error_code: str, error_message: str) -> None:
        JobRepository.update_status(
            job_id,
            status=JobStatus.FAILED,
            progress=100,
            error_code=error_code,
            error_message=error_message,
        )

    @classmethod
    async def submit_task(cls, job_id: str, func: Callable, *args, **kwargs) -> None:
        """Schedules a synchronous CPU/IO heavy task on the thread pool executor."""
        loop = asyncio.get_running_loop()

        def runner():
            try:
                cls.update_progress(job_id, JobStatus.PROCESSING, 30)
                result = func(job_id, *args, **kwargs)
                return result
            except Exception as exc:
                logger.error(f"Job {job_id} failed with error: {exc}")
                error_code = getattr(exc, "code", "PROCESSING_FAILED")
                error_message = getattr(exc, "message", str(exc))
                cls.mark_failed(job_id, error_code, error_message)

        loop.run_in_executor(_executor, runner)

    @staticmethod
    def save_output_file(job_id: str, filename: str, data: bytes) -> Path:
        """Saves generated stego file or extracted payload to disk."""
        job_dir = get_output_dir() / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / filename
        file_path.write_bytes(data)
        return file_path

    @staticmethod
    def get_output_file(job_id: str, filename: str) -> Optional[Path]:
        file_path = get_output_dir() / job_id / filename
        if file_path.exists():
            return file_path
        return None

    @staticmethod
    def cleanup_job_files(job_id: str) -> None:
        job_dir = get_output_dir() / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
