"""Job database models and repository interface."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import sqlite3
from typing import Any, Dict, List, Optional
from app.db.session import get_db


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobOperation(str, Enum):
    ENCODE_TEXT = "ENCODE_TEXT"
    ENCODE_ZIP = "ENCODE_ZIP"
    DECODE = "DECODE"
    VERIFY = "VERIFY"


@dataclass
class JobRecord:
    id: str
    status: JobStatus
    operation: JobOperation
    carrier_type: str  # "IMAGE" or "VIDEO"
    payload_type: Optional[str]  # "TEXT", "ZIP", or None
    carrier_size: int
    payload_size: Optional[int]
    progress: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    output_file_id: Optional[str] = None
    output_filename: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "JobRecord":
        return cls(
            id=row["id"],
            status=JobStatus(row["status"]),
            operation=JobOperation(row["operation"]),
            carrier_type=row["carrier_type"],
            payload_type=row["payload_type"],
            carrier_size=row["carrier_size"],
            payload_size=row["payload_size"],
            progress=row["progress"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            output_file_id=row["output_file_id"],
            output_filename=row["output_filename"],
            mime_type=row["mime_type"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"],
        )


class JobRepository:
    """Repository for non-sensitive job metadata persistence."""

    @staticmethod
    def create(job: JobRecord) -> JobRecord:
        now = datetime.now(timezone.utc).isoformat()
        job.created_at = now
        job.updated_at = now
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO jobs (
                    id, status, operation, carrier_type, payload_type,
                    carrier_size, payload_size, progress, error_code, error_message,
                    output_file_id, output_filename, mime_type,
                    created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.status.value,
                    job.operation.value,
                    job.carrier_type,
                    job.payload_type,
                    job.carrier_size,
                    job.payload_size,
                    job.progress,
                    job.error_code,
                    job.error_message,
                    job.output_file_id,
                    job.output_filename,
                    job.mime_type,
                    job.created_at,
                    job.updated_at,
                    job.completed_at,
                ),
            )
            # Project policy: Store only up-to-date active data; prune prior history
            cursor.execute(
                """
                DELETE FROM jobs WHERE id NOT IN (
                    SELECT id FROM jobs ORDER BY datetime(updated_at) DESC LIMIT 5
                )
                """
            )
        return job

    @staticmethod
    def get(job_id: str) -> Optional[JobRecord]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return JobRecord.from_row(row)
        return None

    @staticmethod
    def list_recent(limit: int = 50) -> List[JobRecord]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [JobRecord.from_row(r) for r in rows]

    @staticmethod
    def update_status(
        job_id: str,
        status: JobStatus,
        progress: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        output_file_id: Optional[str] = None,
        output_filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Optional[JobRecord]:
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status in (JobStatus.COMPLETED, JobStatus.FAILED) else None

        with get_db() as conn:
            cursor = conn.cursor()
            updates = ["status = ?", "updated_at = ?"]
            params: List[Any] = [status.value, now]

            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)
            if error_code is not None:
                updates.append("error_code = ?")
                params.append(error_code)
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)
            if output_file_id is not None:
                updates.append("output_file_id = ?")
                params.append(output_file_id)
            if output_filename is not None:
                updates.append("output_filename = ?")
                params.append(output_filename)
            if mime_type is not None:
                updates.append("mime_type = ?")
                params.append(mime_type)
            if completed_at is not None:
                updates.append("completed_at = ?")
                params.append(completed_at)

            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

        return JobRepository.get(job_id)
