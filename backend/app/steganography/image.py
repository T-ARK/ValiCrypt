"""Lossless Image Steganography Engine using NumPy-vectorized LSB embedding.

Embeds an encrypted MediaVault binary envelope into the least-significant bits (LSB)
of lossless image carriers (PNG, BMP, TIFF) while preserving color fidelity and alpha channel.

Format:
  - 4 bytes magic: b"MVLT"
  - 4 bytes payload length (uint32 big-endian)
  - Followed by exact payload bytes (EncryptedEnvelope)
"""

import io
import struct
from typing import Optional, Tuple
import numpy as np
from PIL import Image
from app.core.errors import (
    CorruptedPayloadError,
    InsufficientCapacityError,
    InvalidFileError,
)

PREAMBLE_MAGIC = b"MVLT"
PREAMBLE_FORMAT = ">4sI"
PREAMBLE_SIZE = struct.calcsize(PREAMBLE_FORMAT)  # 8 bytes (64 bits)


def calculate_image_capacity(width: int, height: int, channels: int) -> int:
    """Calculates usable payload capacity in bytes for given image dimensions.

    Uses 1 bit per usable color channel (RGB for RGB/RGBA; 1 for grayscale).
    Leaves alpha channel untouched.
    """
    usable_channels = 3 if channels in (3, 4) else (1 if channels == 1 else 3)
    total_bits = width * height * usable_channels
    total_bytes = total_bits // 8
    usable_payload_bytes = max(0, total_bytes - PREAMBLE_SIZE)
    return usable_payload_bytes


def inspect_image_carrier(image_bytes: bytes) -> Tuple[int, int, int, str]:
    """Inspects an image carrier and returns (width, height, usable_channels, format)."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            fmt = img.format or "PNG"
            width, height = img.size
            mode = img.mode
            if mode in ("RGB", "YCbCr"):
                channels = 3
            elif mode in ("RGBA", "CMYK"):
                channels = 4
            elif mode in ("L", "1"):
                channels = 1
            else:
                channels = 3
            return width, height, channels, fmt
    except Exception as exc:
        raise InvalidFileError(f"Failed to parse carrier image: {exc}") from exc


def _get_indices(num_bits: int, width: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculates vectorized (row, col, channel) coordinates for LSB bits."""
    pixel_idx = np.arange(num_bits, dtype=np.int64) // 3
    channel_idx = (np.arange(num_bits, dtype=np.int64) % 3).astype(np.int64)
    row_idx = pixel_idx // width
    col_idx = pixel_idx % width
    return row_idx, col_idx, channel_idx


def embed_payload_in_image(image_bytes: bytes, payload_bytes: bytes) -> bytes:
    """Embeds payload into an image carrier and returns PNG-encoded bytes.

    Args:
        image_bytes: Raw bytes of the carrier image.
        payload_bytes: Encrypted payload bytes to embed.

    Returns:
        Lossless PNG bytes containing the steganographic payload.

    Raises:
        InsufficientCapacityError: If payload exceeds carrier capacity.
        InvalidFileError: If carrier is corrupted.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception as exc:
        raise InvalidFileError(f"Failed to open carrier image: {exc}") from exc

    # Ensure RGB or RGBA for lossless encoding
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    arr = np.array(img, dtype=np.uint8)
    height, width, _ = arr.shape

    usable_channels = 3  # Always embed in RGB channels (0, 1, 2)
    max_payload_bytes = calculate_image_capacity(width, height, usable_channels)

    if len(payload_bytes) > max_payload_bytes:
        raise InsufficientCapacityError(
            available_bytes=max_payload_bytes,
            required_bytes=len(payload_bytes),
        )

    # Construct preamble: Magic + 4-byte uint32 payload length
    preamble = struct.pack(PREAMBLE_FORMAT, PREAMBLE_MAGIC, len(payload_bytes))
    full_data = preamble + payload_bytes

    # Unpack bytes into a 1D bit array (uint8 with values 0 or 1)
    data_np = np.frombuffer(full_data, dtype=np.uint8)
    bits = np.unpackbits(data_np).astype(np.uint8)
    num_bits = len(bits)

    # Calculate coordinates
    row_idx, col_idx, channel_idx = _get_indices(num_bits, width)

    # Modify LSBs directly in array
    arr[row_idx, col_idx, channel_idx] = (
        arr[row_idx, col_idx, channel_idx] & np.uint8(0xFE)
    ) | bits

    # Reconstruct Pillow image
    stego_img = Image.fromarray(arr, mode=img.mode)

    # Save to PNG (lossless) in memory
    out_buf = io.BytesIO()
    stego_img.save(out_buf, format="PNG", optimize=False)
    encoded_bytes = out_buf.getvalue()

    # Immediate in-memory roundtrip validation
    extracted_check = extract_payload_from_image(encoded_bytes)
    if extracted_check != payload_bytes:
        raise CorruptedPayloadError(
            "Steganographic verification failed during encoding. Image roundtrip check failed."
        )

    return encoded_bytes


def detect_payload_in_image(image_bytes: bytes) -> Tuple[bool, Optional[int]]:
    """Checks if carrier contains MediaVault preamble without decoding full payload.

    Returns:
        Tuple of (has_payload: bool, payload_length: Optional[int]).
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        height, width, _ = arr.shape

        preamble_bits_count = PREAMBLE_SIZE * 8
        total_available_bits = width * height * 3
        if total_available_bits < preamble_bits_count:
            return False, None

        row_idx, col_idx, channel_idx = _get_indices(preamble_bits_count, width)
        preamble_bits = arr[row_idx, col_idx, channel_idx] & 1
        preamble_bytes = np.packbits(preamble_bits).tobytes()

        magic, payload_len = struct.unpack(PREAMBLE_FORMAT, preamble_bytes)
        if magic == PREAMBLE_MAGIC:
            return True, payload_len
        return False, None
    except Exception:
        return False, None


def extract_payload_from_image(image_bytes: bytes) -> bytes:
    """Extracts embedded payload bytes from an image carrier.

    Args:
        image_bytes: Raw bytes of the steganographic image.

    Returns:
        Raw extracted payload bytes.

    Raises:
        CorruptedPayloadError: If preamble is missing or payload is truncated.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception as exc:
        raise InvalidFileError(f"Failed to open or decode image: {exc}") from exc

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    arr = np.array(img, dtype=np.uint8)
    height, width, _ = arr.shape

    preamble_bits_count = PREAMBLE_SIZE * 8
    total_available_bits = width * height * 3
    if total_available_bits < preamble_bits_count:
        raise CorruptedPayloadError("Image is too small to contain a MediaVault payload.")

    # Read preamble
    row_idx, col_idx, channel_idx = _get_indices(preamble_bits_count, width)
    preamble_bits = arr[row_idx, col_idx, channel_idx] & 1
    preamble_bytes = np.packbits(preamble_bits).tobytes()

    try:
        magic, payload_len = struct.unpack(PREAMBLE_FORMAT, preamble_bytes)
    except Exception as exc:
        raise CorruptedPayloadError("Failed to unpack MediaVault preamble.") from exc

    if magic != PREAMBLE_MAGIC:
        raise CorruptedPayloadError(
            f"No MediaVault payload detected. Expected magic {PREAMBLE_MAGIC!r}, got {magic!r}."
        )

    total_bits_needed = (PREAMBLE_SIZE + payload_len) * 8
    if total_available_bits < total_bits_needed:
        raise CorruptedPayloadError(
            f"Carrier image is truncated: contains {total_available_bits} bits, needed {total_bits_needed} bits."
        )

    # Extract all payload bits (including preamble offset)
    full_row, full_col, full_chan = _get_indices(total_bits_needed, width)
    all_bits = arr[full_row, full_col, full_chan] & 1
    payload_bits = all_bits[preamble_bits_count:]
    extracted_bytes = np.packbits(payload_bits).tobytes()

    if len(extracted_bytes) < payload_len:
        raise CorruptedPayloadError("Extracted data is shorter than declared payload length.")

    return extracted_bytes[:payload_len]
