"""Background job polling and history API routes."""

from typing import List
from fastapi import APIRouter
from app.core.errors import JobNotFoundError
from app.schemas.jobs import JobResponse
from app.services.job_service import JobService

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Retrieves current execution status, progress, and download link for a job."""
    job = JobService.get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)

    download_url = None
    if job.output_filename:
        download_url = f"/api/v1/download/{job.id}/{job.output_filename}"

    return JobResponse(
        id=job.id,
        status=job.status,
        operation=job.operation,
        carrier_type=job.carrier_type,
        payload_type=job.payload_type,
        carrier_size=job.carrier_size,
        payload_size=job.payload_size,
        progress=job.progress,
        error_code=job.error_code,
        error_message=job.error_message,
        download_url=download_url,
        filename=job.output_filename,
        mime_type=job.mime_type,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs", response_model=List[JobResponse], tags=["Jobs"])
async def list_jobs(limit: int = 50):
    """Lists recent operational jobs."""
    jobs = JobService.list_jobs(limit=limit)
    res = []
    for j in jobs:
        d_url = f"/api/v1/download/{j.id}/{j.output_filename}" if j.output_filename else None
        res.append(
            JobResponse(
                id=j.id,
                status=j.status,
                operation=j.operation,
                carrier_type=j.carrier_type,
                payload_type=j.payload_type,
                carrier_size=j.carrier_size,
                payload_size=j.payload_size,
                progress=j.progress,
                error_code=j.error_code,
                error_message=j.error_message,
                download_url=d_url,
                filename=j.output_filename,
                mime_type=j.mime_type,
                created_at=j.created_at,
                updated_at=j.updated_at,
                completed_at=j.completed_at,
            )
        )
    return res
