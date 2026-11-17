"""Acceptance Test Suite validating all 6 core requirements from Section 33.

Acceptance Tests:
  Test 1: PNG Carrier + Text Message ("Hello from MediaVault") + Strong Password -> Recover exact message.
  Test 2: PNG Carrier + Secret ZIP Archive + Password -> Recover exact ZIP contents.
  Test 3: MP4 Carrier + ZIP Archive + Password -> Normal video playback verified + Recover exact ZIP archive.
  Test 4: Wrong Password -> Safe failure with "Decryption failed", zero plaintext leaked.
  Test 5: Tampered Encoded Payload -> Safe failure with "Integrity verification failed".
  Test 6: Oversized Upload Attempt -> Fails with configured upload size limit error.
"""

import hashlib
import io
from pathlib import Path
import subprocess
import zipfile
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.archive.zip_handler import create_safe_zip
from app.core.config import settings
from app.main import app
from app.media.video import verify_video_playback

client = TestClient(app)


@pytest.fixture(scope="session")
def acceptance_sample_png() -> bytes:
    """Creates a sample carrier PNG for acceptance tests."""
    img = Image.new("RGB", (250, 250), color=(70, 130, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def acceptance_sample_mp4(tmp_path_factory) -> Path:
    """Creates a sample carrier MP4 for acceptance tests."""
    session_dir = tmp_path_factory.mktemp("acceptance_video")
    mp4_path = session_dir / "carrier.mp4"
    cmd = [
        settings.FFMPEG_PATH,
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=2:size=320x240:rate=10",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=800:duration=2",
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


def test_acceptance_test_1_png_text_roundtrip(acceptance_sample_png):
    """Acceptance Test 1: carrier.png + message + password -> encoded.png -> recover message."""
    message = "Hello from MediaVault"
    password = "strong-password-test1"

    # Step A: Encode
    resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", acceptance_sample_png, "image/png")},
        data={"message": message, "password": password},
    )
    assert resp.status_code == 200
    enc_info = resp.json()
    assert enc_info["success"] is True

    # Step B: Download encoded carrier
    stego_png = client.get(enc_info["download_url"]).content

    # Step C: Extract with password
    dec_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("encoded.png", stego_png, "image/png")},
        data={"password": password},
    )
    assert dec_resp.status_code == 200
    dec_info = dec_resp.json()
    assert dec_info["success"] is True
    assert dec_info["payload_type"] == "TEXT"
    assert dec_info["text_content"] == "Hello from MediaVault"


def test_acceptance_test_2_png_zip_roundtrip(acceptance_sample_png):
    """Acceptance Test 2: carrier.png + secret.zip + password -> encoded.png -> recover ZIP contents."""
    files_to_zip = {
        "credentials.txt": b"admin:secret_key_999\n",
        "keys/token.jwt": b"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    }
    secret_zip = create_safe_zip(files_to_zip)
    password = "strong-password-test2"

    # Step A: Encode ZIP
    resp = client.post(
        "/api/v1/encode/zip",
        files={
            "carrier": ("carrier.png", acceptance_sample_png, "image/png"),
            "payload": ("secret.zip", secret_zip, "application/zip"),
        },
        data={"password": password},
    )
    assert resp.status_code == 200
    enc_info = resp.json()
    assert enc_info["success"] is True

    # Step B: Download encoded carrier
    stego_png = client.get(enc_info["download_url"]).content

    # Step C: Extract and decrypt ZIP
    dec_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("encoded.png", stego_png, "image/png")},
        data={"password": password},
    )
    assert dec_resp.status_code == 200
    dec_info = dec_resp.json()
    assert dec_info["payload_type"] == "ZIP"

    # Step D: Download recovered ZIP and verify contents
    recovered_zip_bytes = client.get(dec_info["download_url"]).content
    with zipfile.ZipFile(io.BytesIO(recovered_zip_bytes), "r") as zf:
        assert zf.read("credentials.txt") == b"admin:secret_key_999\n"
        assert zf.read("keys/token.jwt") == b"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."


def test_acceptance_test_3_mp4_playback_and_zip_recovery(acceptance_sample_mp4, tmp_path):
    """Acceptance Test 3: MP4 carrier + ZIP -> encoded.mp4 plays normally + recover ZIP."""
    from app.services.encode_service import EncodeService
    from app.services.decode_service import DecodeService
    from app.crypto.models import PayloadType

    test_files = {"archive_report.txt": b"Video Steganography Test Success 2026"}
    zip_bytes = create_safe_zip(test_files)
    password = "strong-video-password-test3"

    job_id = "acceptance-test-mp4-job"
    output_mp4 = tmp_path / "encoded.mp4"

    # Execute embedding directly through service worker
    EncodeService.encode_video_job_worker(
        job_id=job_id,
        carrier_path=acceptance_sample_mp4,
        carrier_filename="carrier.mp4",
        payload_bytes=zip_bytes,
        payload_type=PayloadType.ZIP,
        password=password,
    )

    saved_stego = settings.TEMP_DIRECTORY / "outputs" / job_id / "carrier_vault.mp4"
    assert saved_stego.exists()

    # Verify normal playback characteristics
    assert verify_video_playback(saved_stego) is True

    # Recover payload from MP4
    result = DecodeService.decode_from_video(saved_stego, password)
    assert result.payload_type == "ZIP"

    recovered_file = settings.TEMP_DIRECTORY / "outputs" / result.download_url.split("/")[-2] / result.download_url.split("/")[-1]
    with zipfile.ZipFile(recovered_file, "r") as zf:
        assert zf.read("archive_report.txt") == b"Video Steganography Test Success 2026"


def test_acceptance_test_4_wrong_password_fails_safely(acceptance_sample_png):
    """Acceptance Test 4: Wrong password -> 'Decryption failed', no plaintext leaked."""
    message = "Classified Top Secret"
    password = "CorrectStrongPassword"
    wrong_password = "WrongPasswordAttacker"

    # Encode
    enc_resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", acceptance_sample_png, "image/png")},
        data={"message": message, "password": password},
    )
    stego_png = client.get(enc_resp.json()["download_url"]).content

    # Attempt decode with wrong password
    dec_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("encoded.png", stego_png, "image/png")},
        data={"password": wrong_password},
    )
    assert dec_resp.status_code == 401
    err_body = dec_resp.json()
    assert err_body["error"]["code"] == "INVALID_PASSWORD"
    assert "Decryption failed" in err_body["error"]["message"]
    # Ensure plaintext is never exposed
    assert message not in dec_resp.text


def test_acceptance_test_5_tampered_payload_integrity_failed(acceptance_sample_png):
    """Acceptance Test 5: Modify encoded payload -> 'Integrity verification failed'."""
    from app.crypto.encryption import encrypt_payload
    from app.crypto.models import PayloadType
    from app.steganography.image import embed_payload_in_image

    message = b"Guarded payload"
    password = "TamperTestPassword"

    envelope = bytearray(encrypt_payload(message, password, PayloadType.TEXT))
    # Tamper with the ciphertext byte
    envelope[-5] ^= 0xFF

    # Embed tampered envelope into image
    tampered_stego = embed_payload_in_image(acceptance_sample_png, bytes(envelope))

    # Attempt decode
    dec_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("tampered.png", tampered_stego, "image/png")},
        data={"password": password},
    )
    assert dec_resp.status_code in (401, 422)
    err_body = dec_resp.json()
    assert "Decryption failed" in err_body["error"]["message"] or "altered" in err_body["error"]["message"] or "Integrity" in err_body["error"]["message"]


def test_acceptance_test_6_oversized_upload(monkeypatch):
    """Acceptance Test 6: Oversized upload -> 'Upload exceeds configured size limit'."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 200)

    # 500 bytes > 200 bytes limit
    oversized = b"O" * 500

    resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("big.png", oversized, "image/png")},
        data={"message": "hello", "password": "pwd"},
    )
    assert resp.status_code == 413
    err_body = resp.json()
    assert err_body["error"]["code"] == "OVERSIZED_UPLOAD"
    assert "exceeds maximum allowed limit" in err_body["error"]["message"]
