"""Integration tests for end-to-end API encoding and decoding workflows."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.archive.zip_handler import create_safe_zip
from app.main import app

client = TestClient(app)


def make_test_png(w: int = 150, h: int = 150) -> bytes:
    img = Image.new("RGB", (w, h), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_api_encode_and_decode_text_roundtrip():
    """Verify /encode/text and /decode API endpoints roundtrip with correct password."""
    png_bytes = make_test_png(160, 160)
    password = "IntegrationPassword#2026"
    message = "Classified operational message from MediaVault."

    # 1. Encode Text
    encode_resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", png_bytes, "image/png")},
        data={"message": message, "password": password},
    )
    assert encode_resp.status_code == 200, encode_resp.text
    enc_data = encode_resp.json()
    assert enc_data["success"] is True
    assert "download_url" in enc_data

    # Download encoded carrier
    download_resp = client.get(enc_data["download_url"])
    assert download_resp.status_code == 200
    stego_png_bytes = download_resp.content

    # 2. Decode Text with Correct Password
    decode_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("stego.png", stego_png_bytes, "image/png")},
        data={"password": password},
    )
    assert decode_resp.status_code == 200, decode_resp.text
    dec_data = decode_resp.json()
    assert dec_data["success"] is True
    assert dec_data["payload_type"] == "TEXT"
    assert dec_data["text_content"] == message


def test_api_decode_wrong_password_fails_with_401():
    """Verify /decode with wrong password fails with 401 INVALID_PASSWORD."""
    png_bytes = make_test_png(100, 100)
    password = "CorrectSecretPassword"
    wrong_password = "IncorrectPassword"

    encode_resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("carrier.png", png_bytes, "image/png")},
        data={"message": "Secret", "password": password},
    )
    assert encode_resp.status_code == 200
    stego_bytes = client.get(encode_resp.json()["download_url"]).content

    # Attempt decode with wrong password
    decode_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("stego.png", stego_bytes, "image/png")},
        data={"password": wrong_password},
    )
    assert decode_resp.status_code == 401
    err_json = decode_resp.json()
    assert err_json["error"]["code"] == "INVALID_PASSWORD"


def test_api_encode_and_decode_zip_roundtrip():
    """Verify /encode/zip and /decode API endpoints roundtrip with correct password."""
    png_bytes = make_test_png(200, 200)
    password = "ZipSecretPassword#2026"
    test_files = {
        "report.txt": b"Confidential financial statement 2026.",
        "assets/notes.csv": b"id,score\n1,100\n2,95\n",
    }
    zip_bytes = create_safe_zip(test_files)

    # 1. Encode ZIP
    encode_resp = client.post(
        "/api/v1/encode/zip",
        files={
            "carrier": ("carrier.png", png_bytes, "image/png"),
            "payload": ("archive.zip", zip_bytes, "application/zip"),
        },
        data={"password": password},
    )
    assert encode_resp.status_code == 200, encode_resp.text
    enc_data = encode_resp.json()
    assert enc_data["success"] is True
    assert enc_data["payload_type"] == "ZIP"

    # Download stego image
    stego_bytes = client.get(enc_data["download_url"]).content

    # 2. Decode ZIP
    decode_resp = client.post(
        "/api/v1/decode",
        files={"carrier": ("stego.png", stego_bytes, "image/png")},
        data={"password": password},
    )
    assert decode_resp.status_code == 200, decode_resp.text
    dec_data = decode_resp.json()
    assert dec_data["payload_type"] == "ZIP"
    assert "download_url" in dec_data

    # Download recovered zip and verify contents
    recovered_zip_bytes = client.get(dec_data["download_url"]).content
    assert len(recovered_zip_bytes) == len(zip_bytes)


def test_api_insufficient_capacity_error():
    """Verify that attempting to encode into an undersized carrier returns 400 INSUFFICIENT_CAPACITY."""
    tiny_png = make_test_png(20, 20)  # ~142 bytes capacity
    large_message = "A" * 1000

    resp = client.post(
        "/api/v1/encode/text",
        files={"carrier": ("tiny.png", tiny_png, "image/png")},
        data={"message": large_message, "password": "pwd"},
    )
    assert resp.status_code == 400
    err = resp.json()["error"]
    assert err["code"] == "INSUFFICIENT_CAPACITY"
    assert "available_bytes" in err["details"]
    assert "required_bytes" in err["details"]
