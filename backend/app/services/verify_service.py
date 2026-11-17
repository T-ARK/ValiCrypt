"""Verify Service for inspecting carriers and verifying MediaVault payloads without password."""

from pathlib import Path
from typing import Optional
from app.crypto.envelope import unpack_header
from app.crypto.models import CryptoAlgorithm, KdfAlgorithm, PayloadType
from app.media.video import inspect_video
from app.schemas.jobs import VerifyResponse
from app.steganography.image import (
    detect_payload_in_image,
    extract_payload_from_image,
    inspect_image_carrier,
)
from app.steganography.video import (
    detect_payload_in_video,
    extract_payload_from_video,
)


class VerifyService:
    @staticmethod
    def verify_image(image_bytes: bytes) -> VerifyResponse:
        """Inspects an image carrier and analyzes MediaVault structural metadata."""
        w, h, c, fmt = inspect_image_carrier(image_bytes)
        carrier_props = {"width": w, "height": h, "channels": c, "format": fmt}

        has_payload, declared_len = detect_payload_in_image(image_bytes)
        if not has_payload:
            return VerifyResponse(
                carrier_type="IMAGE",
                media_format=fmt,
                payload_present=False,
                integrity_status="NOT_DETECTED",
                carrier_properties=carrier_props,
            )

        try:
            raw_envelope = extract_payload_from_image(image_bytes)
            header, _ = unpack_header(raw_envelope)

            algo_name = "AES-256-GCM" if header.algorithm == CryptoAlgorithm.AES_256_GCM else "UNKNOWN"
            kdf_name = "Argon2id" if header.kdf == KdfAlgorithm.ARGON2ID else "UNKNOWN"
            p_type_name = header.payload_type.name

            return VerifyResponse(
                carrier_type="IMAGE",
                media_format=fmt,
                mediavault_version=header.version,
                payload_present=True,
                payload_type=p_type_name,
                encryption_algorithm=algo_name,
                kdf_algorithm=kdf_name,
                payload_size_bytes=header.plaintext_length,
                integrity_status="VALID",
                carrier_properties=carrier_props,
            )
        except Exception as exc:
            return VerifyResponse(
                carrier_type="IMAGE",
                media_format=fmt,
                payload_present=True,
                integrity_status="CORRUPTED",
                carrier_properties=carrier_props,
            )

    @staticmethod
    def verify_video(video_path: Path) -> VerifyResponse:
        """Inspects a video carrier and analyzes MediaVault structural metadata."""
        video_props = inspect_video(video_path)
        props_dict = {
            "container": video_props.container,
            "duration": video_props.duration_seconds,
            "size_bytes": video_props.size_bytes,
            "width": video_props.width,
            "height": video_props.height,
            "fps": video_props.fps,
            "video_codec": video_props.video_codec,
            "audio_codec": video_props.audio_codec,
        }

        has_payload, size = detect_payload_in_video(video_path)
        if not has_payload:
            return VerifyResponse(
                carrier_type="VIDEO",
                media_format=video_props.container.upper(),
                payload_present=False,
                integrity_status="NOT_DETECTED",
                carrier_properties=props_dict,
            )

        try:
            raw_envelope = extract_payload_from_video(video_path)
            header, _ = unpack_header(raw_envelope)

            algo_name = "AES-256-GCM" if header.algorithm == CryptoAlgorithm.AES_256_GCM else "UNKNOWN"
            kdf_name = "Argon2id" if header.kdf == KdfAlgorithm.ARGON2ID else "UNKNOWN"
            p_type_name = header.payload_type.name

            return VerifyResponse(
                carrier_type="VIDEO",
                media_format=video_props.container.upper(),
                mediavault_version=header.version,
                payload_present=True,
                payload_type=p_type_name,
                encryption_algorithm=algo_name,
                kdf_algorithm=kdf_name,
                payload_size_bytes=header.plaintext_length,
                integrity_status="VALID",
                carrier_properties=props_dict,
            )
        except Exception:
            return VerifyResponse(
                carrier_type="VIDEO",
                media_format=video_props.container.upper(),
                payload_present=True,
                integrity_status="CORRUPTED",
                carrier_properties=props_dict,
            )
