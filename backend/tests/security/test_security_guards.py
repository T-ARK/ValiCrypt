"""Security tests for MediaVault defenses.

Tests:
  - Path traversal protection in download endpoint
  - Oversized upload rejection
  - Sensitive data log sanitization (no passwords or keys in logs)
  - Tampered payload handling
  - Safe error responses (no stack traces leaked)
"""

import io
from fastapi.testclient import TestClient
from PIL import Image
from app.core.config import settings
from app.core.logging import SecuritySanitizingFilter
from app.main import app

client = TestClient(app)


def test_download_path_traversal_prevention():
    """Attempting path traversal in download endpoint must be blocked."""
    # Attempting to access ../../../../etc/passwd
    resp = client.get("/api/v1/download/test-job/..%2F..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in (400, 404)


def test_oversized_upload_rejection(monkeypatch):
    """Uploads exceeding configured MAX_UPLOAD_SIZE must fail with 413."""
    import app.api.routes.encode as encode_route
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 500)

    # 1000 bytes > 500 bytes limit
    oversized_data = b"X" * 1000

    resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", oversized_data, "image/png")},
        data={"message": "hello", "password": "pwd"},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "OVERSIZED_UPLOAD"


def test_log_sanitizer_redacts_passwords_and_keys():
    """Security filter must redact passwords, secrets, and auth tokens from logs."""
    test_message = "User auth with password='SuperSecretPassword123' and token:abc-123-xyz"
    sanitized = SecuritySanitizingFilter.sanitize(test_message)
    assert "SuperSecretPassword123" not in sanitized
    assert "REDACTED" in sanitized


def test_tampered_stego_carrier_fails_cleanly():
    """Modifying bits in a stego carrier must return a structured 401 or 422 without 500 stacktrace."""
    img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # 1. Encode
    enc_resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("c.png", png_bytes, "image/png")},
        data={"message": "Sensitive payload", "password": "Pass123!@#"},
    )
    stego_bytes = bytearray(client.get(enc_resp.json()["download_url"]).content)

    # 2. Corrupt stego bytes in PNG IDAT data chunk
    # Flip bytes midway
    stego_bytes[len(stego_bytes) // 2] ^= 0xFF

    # 3. Attempt decode
    decode_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("tampered.png", bytes(stego_bytes), "image/png")},
        data={"password": "Pass123!@#"},
    )
    # Must fail safely with a client error (400, 401, or 422), never an unhandled 500
    assert decode_resp.status_code in (400, 401, 422)
    err = decode_resp.json()["error"]
    assert "code" in err
    assert "message" in err
