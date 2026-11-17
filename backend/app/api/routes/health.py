"""Health check and observability API routes."""

from pathlib import Path
from fastapi import APIRouter, Depends
from app.api.dependencies import get_settings
from app.core.config import Settings

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check(settings: Settings = Depends(get_settings)):
    """Health check endpoint exposing system status and external tool availability."""
    ffmpeg_available = Path(settings.FFMPEG_PATH).exists()
    ffprobe_available = Path(settings.FFPROBE_PATH).exists()

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "capabilities": {
            "image_steganography": True,
            "video_steganography": ffmpeg_available,
            "ffmpeg_path": settings.FFMPEG_PATH,
            "ffprobe_path": settings.FFPROBE_PATH,
            "encryption": "AES-256-GCM",
            "kdf": "Argon2id",
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE // (1024 * 1024),
            "max_payload_size_mb": settings.MAX_PAYLOAD_SIZE // (1024 * 1024),
        },
    }
