"""Extraction and Decryption Routes for recovering hidden data from carriers."""

from pathlib import Path
import tempfile
from fastapi import APIRouter, File, Form, UploadFile
from app.core.config import settings
from app.core.errors import OversizedUploadError
from app.schemas.jobs import DecodeResponse
from app.services.decode_service import DecodeService

router = APIRouter()


@router.post("/decode", response_model=DecodeResponse, tags=["Decode"])
async def decode_media(
    carrier: UploadFile = File(...),
    password: str = Form(...),
):
    """Detects, extracts, and decrypts MediaVault payload from an image or video carrier."""
    filename = carrier.filename or "carrier"
    content_type = carrier.content_type or ""
    is_video = content_type.startswith("video/") or filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm"))

    carrier_bytes = await carrier.read()
    if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
        raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)

    if not is_video:
        # Image decode
        return DecodeService.decode_from_image(carrier_bytes=carrier_bytes, password=password)

    # Video decode
    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_vid:
        tmp_vid.write(carrier_bytes)
        tmp_vid_path = Path(tmp_vid.name)

    try:
        return DecodeService.decode_from_video(video_path=tmp_vid_path, password=password)
    finally:
        if tmp_vid_path.exists():
            tmp_vid_path.unlink()
