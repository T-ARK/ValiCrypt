"""Encode Service for embedding encrypted text and ZIP payloads into image and video carriers."""

import hashlib
from pathlib import Path
import tempfile
from typing import Optional
from app.archive.zip_handler import validate_zip_archive
from app.core.config import settings
from app.core.errors import (
    InsufficientCapacityError,
    InvalidFileError,
    OversizedUploadError,
)
from app.core.logging import logger
from app.crypto.encryption import encrypt_payload
from app.crypto.models import PayloadType
from app.db.models import JobOperation, JobRecord, JobStatus
from app.schemas.jobs import EncodeSyncResponse
from app.services.job_service import JobService
from app.steganography.image import (
    calculate_image_capacity,
    embed_payload_in_image,
    inspect_image_carrier,
)
from app.steganography.video import (
    calculate_video_capacity,
    embed_payload_in_video,
)


class EncodeService:
    @staticmethod
    def encode_text_in_image(
        carrier_bytes: bytes,
        carrier_filename: str,
        text_message: str,
        password: str,
    ) -> EncodeSyncResponse:
        """Encrypts a text message and embeds it into an image carrier synchronously."""
        if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
            raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)

        plaintext = text_message.encode("utf-8")
        if len(plaintext) > settings.MAX_PAYLOAD_SIZE:
            raise OversizedUploadError(len(plaintext), settings.MAX_PAYLOAD_SIZE)

        # 1. Encrypt payload
        logger.info("Encrypting text payload with Argon2id + AES-256-GCM")
        encrypted_envelope = encrypt_payload(plaintext, password, PayloadType.TEXT)

        # 2. Check capacity
        w, h, c, fmt = inspect_image_carrier(carrier_bytes)
        cap = calculate_image_capacity(w, h, c)
        if len(encrypted_envelope) > cap:
            raise InsufficientCapacityError(available_bytes=cap, required_bytes=len(encrypted_envelope))

        # 3. Create job record
        job = JobService.create_job(
            operation=JobOperation.ENCODE_TEXT,
            carrier_type="IMAGE",
            carrier_size=len(carrier_bytes),
            payload_type="TEXT",
            payload_size=len(plaintext),
        )

        # 4. Embed into carrier
        logger.info(f"Embedding encrypted payload into image carrier for job {job.id}")
        JobService.update_progress(job.id, JobStatus.PROCESSING, 40)
        encoded_png = embed_payload_in_image(carrier_bytes, encrypted_envelope)

        JobService.update_progress(job.id, JobStatus.VERIFYING, 85)

        # 5. Save output file
        stem = Path(carrier_filename).stem if carrier_filename else "mediavault_image"
        out_name = f"{stem}_vault.png"
        JobService.save_output_file(job.id, out_name, encoded_png)

        # 6. Mark job completed
        JobService.mark_completed(
            job.id,
            output_file_id=job.id,
            output_filename=out_name,
            mime_type="image/png",
        )

        checksum = hashlib.sha256(encoded_png).hexdigest()
        return EncodeSyncResponse(
            job_id=job.id,
            download_url=f"/api/v1/download/{job.id}/{out_name}",
            filename=out_name,
            mime_type="image/png",
            carrier_type="IMAGE",
            payload_type="TEXT",
            output_size_bytes=len(encoded_png),
            sha256_checksum=checksum,
        )

    @staticmethod
    def encode_zip_in_image(
        carrier_bytes: bytes,
        carrier_filename: str,
        zip_bytes: bytes,
        password: str,
    ) -> EncodeSyncResponse:
        """Encrypts a validated ZIP archive and embeds it into an image carrier synchronously."""
        if len(carrier_bytes) > settings.MAX_UPLOAD_SIZE:
            raise OversizedUploadError(len(carrier_bytes), settings.MAX_UPLOAD_SIZE)
        if len(zip_bytes) > settings.MAX_PAYLOAD_SIZE:
            raise OversizedUploadError(len(zip_bytes), settings.MAX_PAYLOAD_SIZE)

        # Validate ZIP
        validate_zip_archive(zip_bytes)

        # Encrypt
        encrypted_envelope = encrypt_payload(zip_bytes, password, PayloadType.ZIP)

        # Capacity check
        w, h, c, fmt = inspect_image_carrier(carrier_bytes)
        cap = calculate_image_capacity(w, h, c)
        if len(encrypted_envelope) > cap:
            raise InsufficientCapacityError(available_bytes=cap, required_bytes=len(encrypted_envelope))

        job = JobService.create_job(
            operation=JobOperation.ENCODE_ZIP,
            carrier_type="IMAGE",
            carrier_size=len(carrier_bytes),
            payload_type="ZIP",
            payload_size=len(zip_bytes),
        )

        JobService.update_progress(job.id, JobStatus.PROCESSING, 40)
        encoded_png = embed_payload_in_image(carrier_bytes, encrypted_envelope)

        JobService.update_progress(job.id, JobStatus.VERIFYING, 85)

        stem = Path(carrier_filename).stem if carrier_filename else "mediavault_image"
        out_name = f"{stem}_vault.png"
        JobService.save_output_file(job.id, out_name, encoded_png)

        JobService.mark_completed(
            job.id,
            output_file_id=job.id,
            output_filename=out_name,
            mime_type="image/png",
        )

        checksum = hashlib.sha256(encoded_png).hexdigest()
        return EncodeSyncResponse(
            job_id=job.id,
            download_url=f"/api/v1/download/{job.id}/{out_name}",
            filename=out_name,
            mime_type="image/png",
            carrier_type="IMAGE",
            payload_type="ZIP",
            output_size_bytes=len(encoded_png),
            sha256_checksum=checksum,
        )

    @classmethod
    def encode_video_job_worker(
        cls,
        job_id: str,
        carrier_path: Path,
        carrier_filename: str,
        payload_bytes: bytes,
        payload_type: PayloadType,
        password: str,
    ) -> None:
        """Worker executing video encoding and playback verification in background thread."""
        try:
            # 1. Encrypt
            encrypted_envelope = encrypt_payload(payload_bytes, password, payload_type)

            # 2. Embed
            JobService.update_progress(job_id, JobStatus.PROCESSING, 50)
            stem = Path(carrier_filename).stem
            ext = Path(carrier_filename).suffix.lower() or ".mp4"
            out_name = f"{stem}_vault{ext}"
            out_path = settings.TEMP_DIRECTORY / "outputs" / job_id / out_name
            out_path.parent.mkdir(parents=True, exist_ok=True)

            embed_payload_in_video(carrier_path, out_path, encrypted_envelope)

            # 3. Mark completed
            mime = "video/mp4" if ext == ".mp4" else ("video/x-matroska" if ext == ".mkv" else "video/quicktime")
            JobService.mark_completed(
                job_id,
                output_file_id=job_id,
                output_filename=out_name,
                mime_type=mime,
            )
            logger.info(f"Video job {job_id} successfully completed.")
        finally:
            # Cleanup input temporary carrier
            if carrier_path.exists():
                carrier_path.unlink()
