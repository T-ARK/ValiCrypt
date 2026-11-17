"""Data Encoding Routes for hiding text and ZIP payloads in image and video carriers."""

from pathlib import Path
import tempfile
from fastapi import APIRouter, File, Form, UploadFile
from app.core.config import settings
from app.core.errors import InvalidFileError, OversizedUploadError
from app.crypto.models import PayloadType
from app.db.models import JobOperation, JobRecord
from app.schemas.jobs import EncodeSyncResponse, JobResponse
from app.services.encode_service import EncodeService
from app.services.job_service import JobService

router = APIRouter()


@router.post("/encode/text", tags=["Encode"])
async def encode_text(
    carrier: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(...),
):
    """Encrypts text message and embeds into image or video carrier."""
    filename = carrier.filename or "carrier"
    content_type = carrier.content_type or ""
    is_video = content_type.startswith("video/") or filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm"))

    carrier_bytes = await carrier.read()
    if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
        raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)

    plaintext = message.encode("utf-8")
    if len(plaintext) > settings.MAX_PAYLOAD_SIZE:
        raise OversizedUploadError(len(plaintext), settings.MAX_PAYLOAD_SIZE)

    if not is_video:
        # Image synchronous encoding
        resp = EncodeService.encode_text_in_image(
            carrier_bytes=carrier_bytes,
            carrier_filename=filename,
            text_message=message,
            password=password,
        )
        return resp

    # Video asynchronous background job
    job = JobService.create_job(
        operation=JobOperation.ENCODE_TEXT,
        carrier_type="VIDEO",
        carrier_size=len(carrier_bytes),
        payload_type="TEXT",
        payload_size=len(plaintext),
    )

    # Save temp carrier file for ffmpeg processing
    ext = Path(filename).suffix.lower() or ".mp4"
    tmp_carrier = settings.TEMP_DIRECTORY / f"input_{job.id}{ext}"
    tmp_carrier.write_bytes(carrier_bytes)

    await JobService.submit_task(
        job.id,
        EncodeService.encode_video_job_worker,
        carrier_path=tmp_carrier,
        carrier_filename=filename,
        payload_bytes=plaintext,
        payload_type=PayloadType.TEXT,
        password=password,
    )

    return JobResponse(
        id=job.id,
        status=job.status,
        operation=job.operation,
        carrier_type=job.carrier_type,
        payload_type=job.payload_type,
        carrier_size=job.carrier_size,
        payload_size=job.payload_size,
        progress=0,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/encode/zip", tags=["Encode"])
async def encode_zip(
    carrier: UploadFile = File(...),
    payload: UploadFile = File(...),
    password: str = Form(...),
):
    """Encrypts ZIP archive and embeds into image or video carrier."""
    filename = carrier.filename or "carrier"
    content_type = carrier.content_type or ""
    is_video = content_type.startswith("video/") or filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm"))

    carrier_bytes = await carrier.read()
    zip_bytes = await payload.read()

    if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
        raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)
    if len(zip_bytes) > settings.MAX_PAYLOAD_SIZE:
        raise OversizedUploadError(len(zip_bytes), settings.MAX_PAYLOAD_SIZE)

    if not is_video:
        resp = EncodeService.encode_zip_in_image(
            carrier_bytes=carrier_bytes,
            carrier_filename=filename,
            zip_bytes=zip_bytes,
            password=password,
        )
        return resp

    # Video asynchronous background job
    job = JobService.create_job(
        operation=JobOperation.ENCODE_ZIP,
        carrier_type="VIDEO",
        carrier_size=len(carrier_bytes),
        payload_type="ZIP",
        payload_size=len(zip_bytes),
    )

    ext = Path(filename).suffix.lower() or ".mp4"
    tmp_carrier = settings.TEMP_DIRECTORY / f"input_{job.id}{ext}"
    tmp_carrier.write_bytes(carrier_bytes)

    await JobService.submit_task(
        job.id,
        EncodeService.encode_video_job_worker,
        carrier_path=tmp_carrier,
        carrier_filename=filename,
        payload_bytes=zip_bytes,
        payload_type=PayloadType.ZIP,
        password=password,
    )

    return JobResponse(
        id=job.id,
        status=job.status,
        operation=job.operation,
        carrier_type=job.carrier_type,
        payload_type=job.payload_type,
        carrier_size=job.carrier_size,
        payload_size=job.payload_size,
        progress=0,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
