"""Unit tests for video steganography engine and FFmpeg integration."""

from pathlib import Path
import subprocess
import tempfile
import pytest
from app.core.config import settings
from app.core.errors import CorruptedPayloadError, InsufficientCapacityError
from app.media.video import inspect_video, verify_video_playback
from app.steganography.video import (
    calculate_video_capacity,
    detect_payload_in_video,
    embed_payload_in_video,
    extract_payload_from_video,
)


@pytest.fixture(scope="session")
def sample_mp4(tmp_path_factory) -> Path:
    """Generates a small valid MP4 test video with audio using FFmpeg."""
    session_dir = tmp_path_factory.mktemp("video_test")
    mp4_path = session_dir / "sample.mp4"
    cmd = [
        settings.FFMPEG_PATH,
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=1:size=320x240:rate=10",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=1",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(mp4_path),
        "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return mp4_path


@pytest.fixture(scope="session")
def sample_mkv(tmp_path_factory, sample_mp4) -> Path:
    """Converts the sample MP4 into MKV format for Matroska tests."""
    session_dir = tmp_path_factory.mktemp("mkv_test")
    mkv_path = session_dir / "sample.mkv"
    cmd = [
        settings.FFMPEG_PATH,
        "-i",
        str(sample_mp4),
        "-c",
        "copy",
        str(mkv_path),
        "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return mkv_path


def test_inspect_video(sample_mp4):
    """Verify video properties can be parsed accurately via ffprobe."""
    props = inspect_video(sample_mp4)
    assert props.has_video is True
    assert props.width == 320
    assert props.height == 240
    assert props.video_codec in ("h264", "libx264")
    assert props.has_audio is True
    assert props.audio_codec == "aac"
    assert props.duration_seconds > 0.5


def test_verify_video_playback(sample_mp4):
    """Verify clean video passes FFmpeg decode verification."""
    assert verify_video_playback(sample_mp4) is True


def test_mp4_embed_extract_and_playback_roundtrip(sample_mp4, tmp_path):
    """Verify embedding in MP4 preserves playback and allows 100% accurate extraction."""
    output_mp4 = tmp_path / "stego.mp4"
    payload = b"VIDEO_STEGANOGRAPHY_SECRET_PAYLOAD_12345_MP4"

    # Embed
    embed_payload_in_video(sample_mp4, output_mp4, payload)
    assert output_mp4.exists()

    # Detect
    detected, size = detect_payload_in_video(output_mp4)
    assert detected is True
    assert size == len(payload)

    # Extract
    extracted = extract_payload_from_video(output_mp4)
    assert extracted == payload

    # Playback check
    assert verify_video_playback(output_mp4) is True


def test_mkv_embed_extract_and_playback_roundtrip(sample_mkv, tmp_path):
    """Verify embedding in MKV container preserves playback and extracts accurately."""
    output_mkv = tmp_path / "stego.mkv"
    payload = b"MKV_ATTACHMENT_SECRET_PAYLOAD_DATA_67890"

    embed_payload_in_video(sample_mkv, output_mkv, payload)
    assert output_mkv.exists()

    detected, size = detect_payload_in_video(output_mkv)
    assert detected is True
    assert size == len(payload)

    extracted = extract_payload_from_video(output_mkv)
    assert extracted == payload

    assert verify_video_playback(output_mkv) is True


def test_extract_clean_video_fails_safely(sample_mp4):
    """Extracting payload from a video with no MediaVault data must fail safely."""
    detected, size = detect_payload_in_video(sample_mp4)
    assert detected is False
    assert size is None

    with pytest.raises(CorruptedPayloadError):
        extract_payload_from_video(sample_mp4)


def test_video_capacity_calculation(sample_mp4):
    """Verify video capacity is reported accurately."""
    cap = calculate_video_capacity(sample_mp4)
    assert cap == settings.MAX_PAYLOAD_SIZE
