"""MediaVault configuration module.

Handles environment variables and system-wide settings using standard Pydantic BaseModel.
"""

from pathlib import Path
import os
import shutil
from typing import List
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # General
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ValiCrypt")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Paths
    BASE_DIR: Path = (
        Path(__file__).resolve().parents[3]
        if (Path(__file__).resolve().parents[3] / "frontend" / "dist").exists()
        else Path(__file__).resolve().parents[2]
    )
    TEMP_DIRECTORY: Path = Path(os.getenv("TEMP_DIRECTORY", "/tmp/mediavault"))

    # Upload & Payload Limits (Bytes)
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 100 * 1024 * 1024))  # 100 MB max carrier upload
    MAX_PAYLOAD_SIZE: int = int(os.getenv("MAX_PAYLOAD_SIZE", 50 * 1024 * 1024))  # 50 MB max payload size
    MAX_ZIP_EXTRACTED_SIZE: int = int(os.getenv("MAX_ZIP_EXTRACTED_SIZE", 100 * 1024 * 1024))  # 100MB max uncompressed

    # Argon2id Parameters (RFC 9106 recommended values)
    ARGON2_TIME_COST: int = int(os.getenv("ARGON2_TIME_COST", "2"))
    ARGON2_MEMORY_COST: int = int(os.getenv("ARGON2_MEMORY_COST", "65536"))  # 64 MiB in KiB
    ARGON2_PARALLELISM: int = int(os.getenv("ARGON2_PARALLELISM", "4"))
    ARGON2_SALT_BYTES: int = 16
    AES_KEY_BYTES: int = 32  # 256-bit key
    AES_NONCE_BYTES: int = 12  # 96-bit nonce for AES-GCM

    # Tool Binaries
    FFMPEG_PATH: str = Field(
        default_factory=lambda: (
            os.getenv("FFMPEG_PATH")
            or shutil.which("ffmpeg")
            or (str(Path(__file__).resolve().parents[3] / "bin" / "ffmpeg") if (Path(__file__).resolve().parents[3] / "bin" / "ffmpeg").exists() else "ffmpeg")
        )
    )
    FFPROBE_PATH: str = Field(
        default_factory=lambda: (
            os.getenv("FFPROBE_PATH")
            or shutil.which("ffprobe")
            or (str(Path(__file__).resolve().parents[3] / "bin" / "ffprobe") if (Path(__file__).resolve().parents[3] / "bin" / "ffprobe").exists() else "ffprobe")
        )
    )

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mediavault.db")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]


settings = Settings()
settings.TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)
