"""FFmpeg and ffprobe wrapper for video validation, property inspection, and playback checks."""

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.errors import InvalidFileError, UnsupportedFormatError, VideoProcessingError
from app.core.logging import logger

SUPPORTED_CONTAINERS = {"mp4", "mkv", "matroska", "mov", "m4v", "webm"}


@dataclass
class VideoProperties:
    container: str
    duration_seconds: float
    size_bytes: int
    bitrate: int
    has_video: bool
    video_codec: Optional[str]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    has_audio: bool
    audio_codec: Optional[str]
    raw_streams: List[Dict[str, Any]]


def run_command_secure(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Executes external binary via subprocess array without shell invocation."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res
    except subprocess.CalledProcessError as exc:
        logger.error(f"Command failed: {' '.join(cmd[:2])}... Stderr: {exc.stderr}")
        raise


def inspect_video(file_path: Path) -> VideoProperties:
    """Inspects video container and stream properties using ffprobe.

    Args:
        file_path: Path to the target video file.

    Returns:
        VideoProperties object.

    Raises:
        InvalidFileError: If ffprobe cannot parse the file.
        UnsupportedFormatError: If the container format is unsupported.
    """
    if not file_path.exists():
        raise InvalidFileError(f"Video file does not exist: {file_path}")

    cmd = [
        settings.FFPROBE_PATH,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    try:
        proc = run_command_secure(cmd, check=True)
        probe_data = json.loads(proc.stdout)
    except Exception as exc:
        raise InvalidFileError(f"ffprobe failed to inspect media: {exc}") from exc

    fmt_info = probe_data.get("format", {})
    format_names = fmt_info.get("format_name", "").lower().split(",")
    matched_container = next((c for c in format_names if c in SUPPORTED_CONTAINERS), None)

    if not matched_container:
        raise UnsupportedFormatError(
            f"Unsupported video container '{fmt_info.get('format_name')}'. Supported: {sorted(SUPPORTED_CONTAINERS)}"
        )

    streams = probe_data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream:
        raise InvalidFileError("Provided file contains no video streams.")

    # Parse fps
    fps = None
    r_frame_rate = video_stream.get("r_frame_rate", "")
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        try:
            if float(den) > 0:
                fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            fps = None

    return VideoProperties(
        container=matched_container,
        duration_seconds=float(fmt_info.get("duration", 0.0)),
        size_bytes=int(fmt_info.get("size", file_path.stat().st_size)),
        bitrate=int(fmt_info.get("bit_rate", 0)),
        has_video=True,
        video_codec=video_stream.get("codec_name"),
        width=video_stream.get("width"),
        height=video_stream.get("height"),
        fps=fps,
        has_audio=audio_stream is not None,
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        raw_streams=streams,
    )


def verify_video_playback(file_path: Path) -> bool:
    """Verifies that the video file can be decoded cleanly by FFmpeg.

    Runs FFmpeg with the null muxer to decode frames and ensure playback integrity.
    """
    cmd = [
        settings.FFMPEG_PATH,
        "-v",
        "error",
        "-i",
        str(file_path),
        "-f",
        "null",
        "-",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logger.warning(f"Video verification warning: {proc.stderr}")
            return False
        return True
    except Exception as exc:
        raise VideoProcessingError(f"Playback verification encountered an error: {exc}") from exc
