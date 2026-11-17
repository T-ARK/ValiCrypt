"""Decode Service for detecting, extracting, and decrypting MediaVault payloads."""

import hashlib
from pathlib import Path
from typing import Optional
import uuid
from app.archive.zip_handler import validate_zip_archive
from app.core.config import settings
from app.core.errors import (
    CorruptedPayloadError,
    InvalidFileError,
    InvalidPasswordError,
)
from app.core.logging import logger
from app.crypto.encryption import decrypt_payload
from app.crypto.models import PayloadType
from app.schemas.jobs import DecodeResponse
from app.services.job_service import JobService
from app.steganography.image import extract_payload_from_image
from app.steganography.video import extract_payload_from_video


class DecodeService:
    @staticmethod
    def decode_from_image(carrier_bytes: bytes, password: str) -> DecodeResponse:
        """Extracts and decrypts payload from an image carrier."""
        logger.info("Extracting payload from image carrier")
        raw_envelope = extract_payload_from_image(carrier_bytes)

        logger.info("Decrypting extracted envelope with AES-256-GCM")
        decrypted = decrypt_payload(raw_envelope, password)

        if decrypted.payload_type == PayloadType.TEXT:
            try:
                text_content = decrypted.data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CorruptedPayloadError("Decrypted text is not valid UTF-8.") from exc

            return DecodeResponse(
                success=True,
                payload_type="TEXT",
                text_content=text_content,
                sha256_checksum=decrypted.plaintext_sha256,
                metadata={"length_chars": len(text_content)},
            )

        elif decrypted.payload_type == PayloadType.ZIP:
            # Validate ZIP structure and safety
            file_count, total_uncompressed, safe_names = validate_zip_archive(decrypted.data)

            # Save safe ZIP file for download
            file_id = str(uuid.uuid4())
            filename = f"mediavault_recovered_{file_id[:8]}.zip"
            JobService.save_output_file(file_id, filename, decrypted.data)

            return DecodeResponse(
                success=True,
                payload_type="ZIP",
                download_url=f"/api/v1/download/{file_id}/{filename}",
                filename=filename,
                file_size_bytes=len(decrypted.data),
                sha256_checksum=decrypted.plaintext_sha256,
                metadata={
                    "file_count": file_count,
                    "uncompressed_bytes": total_uncompressed,
                    "files": safe_names[:20],
                },
            )

        else:
            # Generic binary
            file_id = str(uuid.uuid4())
            filename = f"mediavault_recovered_{file_id[:8]}.bin"
            JobService.save_output_file(file_id, filename, decrypted.data)
            return DecodeResponse(
                success=True,
                payload_type="BINARY",
                download_url=f"/api/v1/download/{file_id}/{filename}",
                filename=filename,
                file_size_bytes=len(decrypted.data),
                sha256_checksum=decrypted.plaintext_sha256,
            )

    @staticmethod
    def decode_from_video(video_path: Path, password: str) -> DecodeResponse:
        """Extracts and decrypts payload from a video carrier."""
        logger.info(f"Extracting payload from video carrier: {video_path.name}")
        raw_envelope = extract_payload_from_video(video_path)

        logger.info("Decrypting video envelope with AES-256-GCM")
        decrypted = decrypt_payload(raw_envelope, password)

        if decrypted.payload_type == PayloadType.TEXT:
            try:
                text_content = decrypted.data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CorruptedPayloadError("Decrypted text is not valid UTF-8.") from exc

            return DecodeResponse(
                success=True,
                payload_type="TEXT",
                text_content=text_content,
                sha256_checksum=decrypted.plaintext_sha256,
                metadata={"length_chars": len(text_content)},
            )

        elif decrypted.payload_type == PayloadType.ZIP:
            file_count, total_uncompressed, safe_names = validate_zip_archive(decrypted.data)
            file_id = str(uuid.uuid4())
            filename = f"mediavault_recovered_{file_id[:8]}.zip"
            JobService.save_output_file(file_id, filename, decrypted.data)

            return DecodeResponse(
                success=True,
                payload_type="ZIP",
                download_url=f"/api/v1/download/{file_id}/{filename}",
                filename=filename,
                file_size_bytes=len(decrypted.data),
                sha256_checksum=decrypted.plaintext_sha256,
                metadata={
                    "file_count": file_count,
                    "uncompressed_bytes": total_uncompressed,
                    "files": safe_names[:20],
                },
            )

        else:
            file_id = str(uuid.uuid4())
            filename = f"mediavault_recovered_{file_id[:8]}.bin"
            JobService.save_output_file(file_id, filename, decrypted.data)
            return DecodeResponse(
                success=True,
                payload_type="BINARY",
                download_url=f"/api/v1/download/{file_id}/{filename}",
                filename=filename,
                file_size_bytes=len(decrypted.data),
                sha256_checksum=decrypted.plaintext_sha256,
            )
