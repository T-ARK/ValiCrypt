"""Unit tests for image steganography engine."""

import io
import pytest
from PIL import Image
from app.core.errors import (
    CorruptedPayloadError,
    InsufficientCapacityError,
    InvalidFileError,
)
from app.steganography.image import (
    calculate_image_capacity,
    detect_payload_in_image,
    embed_payload_in_image,
    extract_payload_from_image,
    inspect_image_carrier,
)


def create_test_image_bytes(width: int = 100, height: int = 100, mode: str = "RGB") -> bytes:
    """Helper to create an in-memory PNG image."""
    img = Image.new(mode, (width, height), color=(128, 64, 32) if mode == "RGB" else (128, 64, 32, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_calculate_image_capacity():
    """Verify capacity formula for standard dimensions."""
    # 100x100 RGB = 10,000 pixels * 3 channels = 30,000 bits = 3750 bytes - 8 preamble = 3742 bytes
    cap = calculate_image_capacity(100, 100, 3)
    assert cap == (100 * 100 * 3 // 8) - 8


def test_inspect_image_carrier():
    """Verify inspection returns correct dimensions and channels."""
    img_bytes = create_test_image_bytes(120, 80, "RGB")
    w, h, c, fmt = inspect_image_carrier(img_bytes)
    assert w == 120
    assert h == 80
    assert c == 3
    assert fmt.upper() == "PNG"


def test_image_embed_and_extract_roundtrip():
    """Verify payload embeds into image and extracts with 100% bit-exact accuracy."""
    img_bytes = create_test_image_bytes(150, 150, "RGB")
    payload = b"SUPER_SECRET_PAYLOAD_IMAGE_ROUNDTRIP_TEST_12345"
    
    encoded_png = embed_payload_in_image(img_bytes, payload)
    assert len(encoded_png) > 0
    
    # Detect payload
    has_payload, length = detect_payload_in_image(encoded_png)
    assert has_payload is True
    assert length == len(payload)
    
    # Extract payload
    recovered = extract_payload_from_image(encoded_png)
    assert recovered == payload


def test_rgba_image_support_and_alpha_preservation():
    """Verify RGBA image embeds correctly without altering alpha channel."""
    img_bytes = create_test_image_bytes(80, 80, "RGBA")
    payload = b"RGBA_PAYLOAD_TEST_DATA"
    
    encoded_png = embed_payload_in_image(img_bytes, payload)
    
    # Verify Pillow can open resulting image and mode remains RGBA
    with Image.open(io.BytesIO(encoded_png)) as img:
        assert img.mode == "RGBA"
        # Check alpha channel is preserved at 255
        alpha_band = img.split()[-1]
        assert min(alpha_band.getdata()) == 255
        
    recovered = extract_payload_from_image(encoded_png)
    assert recovered == payload


def test_insufficient_capacity_raises_error():
    """Embedding payload exceeding available capacity must raise InsufficientCapacityError."""
    # 20x20 RGB image capacity = (20*20*3 // 8) - 8 = 150 - 8 = 142 bytes
    img_bytes = create_test_image_bytes(20, 20, "RGB")
    oversized_payload = b"X" * 500  # 500 bytes > 142 bytes
    
    with pytest.raises(InsufficientCapacityError) as exc_info:
        embed_payload_in_image(img_bytes, oversized_payload)
        
    err = exc_info.value
    assert err.code == "INSUFFICIENT_CAPACITY"
    assert err.details["available_bytes"] < 500
    assert err.details["required_bytes"] == 500


def test_extract_from_clean_image_fails_safely():
    """Extracting from an image without MediaVault payload must raise CorruptedPayloadError."""
    clean_img_bytes = create_test_image_bytes(50, 50, "RGB")
    
    has_payload, length = detect_payload_in_image(clean_img_bytes)
    assert has_payload is False
    assert length is None
    
    with pytest.raises(CorruptedPayloadError):
        extract_payload_from_image(clean_img_bytes)


def test_corrupted_carrier_fails():
    """Corrupted carrier bytes must fail with InvalidFileError."""
    corrupted_bytes = b"NOT_AN_IMAGE_RANDOM_GARBAGE"
    with pytest.raises(InvalidFileError):
        embed_payload_in_image(corrupted_bytes, b"payload")
