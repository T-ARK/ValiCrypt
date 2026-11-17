"""Carrier inspection and non-authenticated technical verification routes."""

from pathlib import Path
import tempfile
from fastapi import APIRouter, File, UploadFile
from app.core.config import settings
from app.core.errors import OversizedUploadError
from app.schemas.jobs import VerifyResponse
from app.services.verify_service import VerifyService

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse, tags=["Verification"])
async def verify_carrier(carrier: UploadFile = File(...)):
    """Inspects a media carrier to detect MediaVault envelopes and structural properties."""
    filename = carrier.filename or "carrier"
    content_type = carrier.content_type or ""
    is_video = content_type.startswith("video/") or filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm"))

    carrier_bytes = await carrier.read()
    if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
        raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)

    if not is_video:
        return VerifyService.verify_image(carrier_bytes)

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_vid:
        tmp_vid.write(carrier_bytes)
        tmp_vid_path = Path(tmp_vid.name)

    try:
        return VerifyService.verify_video(tmp_vid_path)
    finally:
        if tmp_vid_path.exists():
            tmp_vid_path.unlink()
