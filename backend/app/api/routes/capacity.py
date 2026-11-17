"""Carrier capacity calculation endpoints."""

from pathlib import Path
import tempfile
from fastapi import APIRouter, File, Form, UploadFile
from app.core.config import settings
from app.core.errors import InvalidFileError, OversizedUploadError
from app.schemas.jobs import CapacityResponse
from app.steganography.image import calculate_image_capacity, inspect_image_carrier
from app.steganography.video import calculate_video_capacity

router = APIRouter()


def format_bytes(num: int) -> str:
    """Formats raw byte count into human-readable string (KB, MB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


@router.post("/capacity", response_model=CapacityResponse, tags=["Steganography"])
async def check_carrier_capacity(
    carrier: UploadFile = File(...),
    payload_size: int = Form(0),
):
    """Calculates available payload capacity for an uploaded image or video carrier."""
    content_type = carrier.content_type or ""
    filename = carrier.filename or "unknown"
    is_video = content_type.startswith("video/") or filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm"))

    carrier_bytes = await carrier.read()
    carrier_size = len(carrier_bytes)

    if carrier_size > settings.MAX_UPLOAD_SIZE:
        raise OversizedUploadError(carrier_size, settings.MAX_UPLOAD_SIZE)

    if is_video:
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_vid:
            tmp_vid.write(carrier_bytes)
            tmp_path = Path(tmp_vid.name)

        try:
            available_cap = calculate_video_capacity(tmp_path)
            return CapacityResponse(
                carrier_type="VIDEO",
                carrier_size_bytes=carrier_size,
                available_capacity_bytes=available_cap,
                available_capacity_human=format_bytes(available_cap),
                sufficient=available_cap >= payload_size,
                carrier_info={"container": Path(filename).suffix.lstrip(".").upper()},
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    else:
        # Image
        w, h, c, fmt = inspect_image_carrier(carrier_bytes)
        available_cap = calculate_image_capacity(w, h, c)
        return CapacityResponse(
            carrier_type="IMAGE",
            carrier_size_bytes=carrier_size,
            available_capacity_bytes=available_cap,
            available_capacity_human=format_bytes(available_cap),
            sufficient=available_cap >= payload_size,
            carrier_info={"width": w, "height": h, "channels": c, "format": fmt},
        )
