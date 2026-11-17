"""Video Steganography Engine.

Implements standards-compliant steganographic embedding for video carriers:
  1. MP4 / MOV / M4V: ISO Base Media File Format (ISO/IEC 14496-12) custom UUID extension box.
     - Preserves 100% video and audio streams without lossy re-encoding.
     - Fully compliant with ISO-BMFF parsers (QuickTime, VLC, HTML5, FFmpeg).
  2. MKV / WebM: Matroska native attachment stream multiplexing via FFmpeg.
     - Preserves all video, audio, and subtitle tracks via stream copy (-c copy).

Every operation verifies round-trip decodability and confirms normal video playback using FFmpeg.
"""

from pathlib import Path
import struct
import subprocess
import tempfile
from typing import Optional, Tuple
from app.core.config import settings
from app.core.errors import (
    CorruptedPayloadError,
    InsufficientCapacityError,
    InvalidFileError,
    VideoProcessingError,
)
from app.core.logging import logger
from app.media.video import inspect_video, verify_video_playback

# Fixed 16-byte UUID identifying MediaVault payload in ISO-BMFF containers
MEDIAVAULT_UUID = b"MediaVault\x01\x02\x03\x04\x05\x06"  # 16 bytes exactly
ISO_BOX_HEADER_SIZE = 8  # 4 bytes size + 4 bytes fourcc ('uuid')
UUID_SIZE = 16


def calculate_video_capacity(carrier_path: Path) -> int:
    """Calculates available payload capacity for the given video file.

    For container-level steganography, capacity is governed by configured MAX_PAYLOAD_SIZE.
    """
    props = inspect_video(carrier_path)
    # Ensure carrier itself is not corrupt
    if props.size_bytes <= 0:
        return 0
    return settings.MAX_PAYLOAD_SIZE


def _embed_mp4_uuid_box(carrier_path: Path, output_path: Path, payload_bytes: bytes) -> None:
    """Embeds payload into an MP4/MOV container as an ISO-BMFF UUID box."""
    with open(carrier_path, "rb") as f:
        media_bytes = f.read()

    # Construct ISO-BMFF UUID box: [4B len][b'uuid'][16B UUID][payload]
    box_total_len = ISO_BOX_HEADER_SIZE + UUID_SIZE + len(payload_bytes)
    uuid_box = struct.pack(">I", box_total_len) + b"uuid" + MEDIAVAULT_UUID + payload_bytes

    # Append UUID box to the ISO-BMFF container sequence
    with open(output_path, "wb") as f:
        f.write(media_bytes)
        f.write(uuid_box)


def _extract_mp4_uuid_box(video_path: Path) -> Optional[bytes]:
    """Scans MP4 container for MediaVault UUID box."""
    with open(video_path, "rb") as f:
        data = f.read()

    pos = 0
    total_len = len(data)
    while pos + ISO_BOX_HEADER_SIZE <= total_len:
        b_len = struct.unpack(">I", data[pos : pos + 4])[0]
        b_type = data[pos + 4 : pos + 8]

        # Handle special ISO box length cases
        if b_len == 1:
            # 64-bit extended size
            if pos + 16 > total_len:
                break
            b_len = struct.unpack(">Q", data[pos + 8 : pos + 16])[0]
            header_offset = 16
        elif b_len == 0:
            # Box extends to EOF
            b_len = total_len - pos
            header_offset = 8
        else:
            header_offset = 8

        if b_len < header_offset:
            break

        if b_type == b"uuid":
            uuid_found = data[pos + header_offset : pos + header_offset + UUID_SIZE]
            if uuid_found == MEDIAVAULT_UUID:
                payload_start = pos + header_offset + UUID_SIZE
                payload_end = pos + b_len
                return data[payload_start:payload_end]

        pos += b_len

    return None


def _embed_mkv_attachment(carrier_path: Path, output_path: Path, payload_bytes: bytes) -> None:
    """Embeds payload into an MKV container using FFmpeg's native attachment stream."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp_payload:
        tmp_payload.write(payload_bytes)
        tmp_payload_path = Path(tmp_payload.name)

    try:
        cmd = [
            settings.FFMPEG_PATH,
            "-i",
            str(carrier_path),
            "-attach",
            str(tmp_payload_path),
            "-metadata:s:t",
            "mimetype=application/octet-stream",
            "-metadata:s:t",
            "filename=mediavault.bin",
            "-c",
            "copy",
            str(output_path),
            "-y",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise VideoProcessingError(f"FFmpeg failed to attach payload to MKV: {proc.stderr}")
    finally:
        if tmp_payload_path.exists():
            tmp_payload_path.unlink()


def _extract_mkv_attachment(video_path: Path) -> Optional[bytes]:
    """Extracts attachment from MKV container using FFmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp_dump:
        tmp_dump_path = Path(tmp_dump.name)

    try:
        cmd = [
            settings.FFMPEG_PATH,
            "-dump_attachment:t:0",
            str(tmp_dump_path),
            "-i",
            str(video_path),
            "-f",
            "null",
            "-",
            "-y",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and tmp_dump_path.exists() and tmp_dump_path.stat().st_size > 0:
            return tmp_dump_path.read_bytes()
        return None
    finally:
        if tmp_dump_path.exists():
            tmp_dump_path.unlink()


def embed_payload_in_video(carrier_path: Path, output_path: Path, payload_bytes: bytes) -> None:
    """Embeds an encrypted payload into a video carrier and validates playback.

    Args:
        carrier_path: Path to input carrier video.
        output_path: Path to destination stego video.
        payload_bytes: Encrypted payload bytes to embed.

    Raises:
        InsufficientCapacityError: If payload exceeds max size.
        InvalidFileError: If carrier is corrupt.
        CorruptedPayloadError: If round-trip validation fails.
    """
    capacity = calculate_video_capacity(carrier_path)
    if len(payload_bytes) > capacity:
        raise InsufficientCapacityError(available_bytes=capacity, required_bytes=len(payload_bytes))

    props = inspect_video(carrier_path)
    container = props.container.lower()

    if container in ("mp4", "mov", "m4v"):
        _embed_mp4_uuid_box(carrier_path, output_path, payload_bytes)
    elif container in ("mkv", "matroska", "webm"):
        _embed_mkv_attachment(carrier_path, output_path, payload_bytes)
    else:
        # Fallback to MP4 UUID if container format allows ISO structure
        _embed_mp4_uuid_box(carrier_path, output_path, payload_bytes)

    # 1. Immediate in-memory extraction validation
    extracted = extract_payload_from_video(output_path)
    if extracted != payload_bytes:
        if output_path.exists():
            output_path.unlink()
        raise CorruptedPayloadError(
            "Video steganographic verification failed during encoding. Extracted payload did not match."
        )

    # 2. Immediate playback integrity check
    if not verify_video_playback(output_path):
        if output_path.exists():
            output_path.unlink()
        raise VideoProcessingError("Embedded video failed FFmpeg playback verification.")

    logger.info(f"Video embedding and playback verification successful for {output_path.name}")


def detect_payload_in_video(video_path: Path) -> Tuple[bool, Optional[int]]:
    """Detects whether video contains MediaVault payload without decrypting."""
    try:
        payload = _extract_mp4_uuid_box(video_path)
        if payload is not None:
            return True, len(payload)
        mkv_payload = _extract_mkv_attachment(video_path)
        if mkv_payload is not None:
            return True, len(mkv_payload)
        return False, None
    except Exception:
        return False, None


def extract_payload_from_video(video_path: Path) -> bytes:
    """Extracts payload bytes from a video carrier.

    Raises:
        CorruptedPayloadError: If no payload is found or extraction fails.
    """
    if not video_path.exists():
        raise InvalidFileError(f"Video file does not exist: {video_path}")

    # Check MP4 ISO-BMFF UUID box first
    payload = _extract_mp4_uuid_box(video_path)
    if payload is not None:
        return payload

    # Check MKV attachment
    mkv_payload = _extract_mkv_attachment(video_path)
    if mkv_payload is not None:
        return mkv_payload

    raise CorruptedPayloadError("No MediaVault payload detected in video file.")
