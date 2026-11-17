"""Integration tests for verification, capacity, and health APIs."""

import io
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)


def make_test_png(w: int = 100, h: int = 100) -> bytes:
    img = Image.new("RGB", (w, h), color=(50, 80, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_api_health_endpoint():
    """Verify /health returns 200 with service info and stego capabilities."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] in ("MediaVault", "ValiCrypt")
    assert data["capabilities"]["image_steganography"] is True
    assert data["capabilities"]["video_steganography"] is True


def test_api_capacity_endpoint():
    """Verify /capacity endpoint accurately computes available space."""
    png_bytes = make_test_png(200, 150)
    resp = client.post(
        "/api/v1/capacity",
        files={"carrier": ("carrier.png", png_bytes, "image/png")},
        data={"payload_size": 500},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["carrier_type"] == "IMAGE"
    assert data["available_capacity_bytes"] > 500
    assert data["sufficient"] is True
    assert "available_capacity_human" in data


def test_api_verify_clean_carrier():
    """Verify /verify detects no payload in a fresh carrier."""
    clean_png = make_test_png(120, 120)
    resp = client.post(
        "/api/v1/verify",
        files={"carrier": ("clean.png", clean_png, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["payload_present"] is False
    assert data["integrity_status"] == "NOT_DETECTED"


def test_api_verify_stego_carrier():
    """Verify /verify detects presence of payload, type, and algorithm without password."""
    png_bytes = make_test_png(150, 150)
    encode_resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", png_bytes, "image/png")},
        data={"message": "Verification secret message", "password": "SecurePassword123"},
    )
    assert encode_resp.status_code == 200
    stego_png = client.get(encode_resp.json()["download_url"]).content

    # Call verify endpoint without password
    verify_resp = client.post(
        "/api/v1/verify",
        files={"carrier": ("stego.png", stego_png, "image/png")},
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["payload_present"] is True
    assert data["mediavault_version"] == 1
    assert data["payload_type"] == "TEXT"
    assert data["encryption_algorithm"] == "AES-256-GCM"
    assert data["kdf_algorithm"] == "Argon2id"
    assert data["integrity_status"] == "VALID"
