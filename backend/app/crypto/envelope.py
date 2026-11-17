"""Binary envelope specification and serializer for MediaVault payloads.

Layout:
  - Magic (4 bytes): b"MV01"
  - Format Version (1 byte): 1
  - Crypto Algorithm (1 byte): 1 (AES-256-GCM)
  - KDF Algorithm (1 byte): 1 (Argon2id)
  - Payload Type (1 byte): 1=Text, 2=ZIP, 3=Binary
  - KDF Time Cost (4 bytes uint32)
  - KDF Memory Cost (4 bytes uint32 in KiB)
  - KDF Parallelism (4 bytes uint32)
  - Salt (16 bytes)
  - Nonce (12 bytes)
  - Plaintext Length (8 bytes uint64)
  - Ciphertext Length (4 bytes uint32, includes 16-byte GCM tag)
  - Plaintext SHA-256 Checksum (32 bytes)
  - Followed by Ciphertext + Auth Tag (N bytes)
"""

import struct
from typing import Tuple
from app.core.errors import CorruptedPayloadError, InvalidPayloadError
from app.crypto.models import (
    CryptoAlgorithm,
    EncryptedEnvelope,
    EnvelopeHeader,
    KdfAlgorithm,
    PayloadType,
)

HEADER_MAGIC = b"MV01"
CURRENT_VERSION = 1
HEADER_FORMAT = ">4sBBBBIII16s12sQI32s"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 92 bytes
MIN_CIPHERTEXT_SIZE = 16  # AES-GCM 16-byte auth tag


def pack_header(header: EnvelopeHeader) -> bytes:
    """Serializes EnvelopeHeader into exact 92-byte binary representation."""
    return struct.pack(
        HEADER_FORMAT,
        header.magic,
        header.version,
        int(header.algorithm),
        int(header.kdf),
        int(header.payload_type),
        header.time_cost,
        header.memory_cost,
        header.parallelism,
        header.salt,
        header.nonce,
        header.plaintext_length,
        header.ciphertext_length,
        header.plaintext_sha256,
    )


def unpack_header(data: bytes) -> Tuple[EnvelopeHeader, bytes]:
    """Unpacks binary data into EnvelopeHeader and validates structure.

    Args:
        data: Raw byte stream containing at least 92 bytes.

    Returns:
        Tuple of (EnvelopeHeader, header_bytes).

    Raises:
        InvalidPayloadError / CorruptedPayloadError if header is invalid.
    """
    if len(data) < HEADER_SIZE:
        raise InvalidPayloadError(
            f"Data size ({len(data)} bytes) is smaller than MediaVault header ({HEADER_SIZE} bytes)."
        )

    header_bytes = data[:HEADER_SIZE]
    (
        magic,
        version,
        algo_val,
        kdf_val,
        type_val,
        time_cost,
        memory_cost,
        parallelism,
        salt,
        nonce,
        plaintext_len,
        ciphertext_len,
        plaintext_sha,
    ) = struct.unpack(HEADER_FORMAT, header_bytes)

    if magic != HEADER_MAGIC:
        raise CorruptedPayloadError(
            f"Invalid magic bytes '{magic!r}'. Expected '{HEADER_MAGIC!r}'."
        )

    if version != CURRENT_VERSION:
        raise CorruptedPayloadError(f"Unsupported MediaVault version: {version}.")

    try:
        algo = CryptoAlgorithm(algo_val)
    except ValueError:
        raise CorruptedPayloadError(f"Unsupported cryptographic algorithm ID: {algo_val}.")

    try:
        kdf = KdfAlgorithm(kdf_val)
    except ValueError:
        raise CorruptedPayloadError(f"Unsupported KDF algorithm ID: {kdf_val}.")

    try:
        payload_type = PayloadType(type_val)
    except ValueError:
        raise CorruptedPayloadError(f"Unknown payload type ID: {type_val}.")

    if ciphertext_len < MIN_CIPHERTEXT_SIZE:
        raise CorruptedPayloadError("Ciphertext length is less than GCM tag size (16 bytes).")

    header = EnvelopeHeader(
        magic=magic,
        version=version,
        algorithm=algo,
        kdf=kdf,
        payload_type=payload_type,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        salt=salt,
        nonce=nonce,
        plaintext_length=plaintext_len,
        ciphertext_length=ciphertext_len,
        plaintext_sha256=plaintext_sha,
    )
    return header, header_bytes


def pack_envelope(header: EnvelopeHeader, ciphertext: bytes) -> bytes:
    """Combines serialized header and ciphertext into single payload."""
    header_bytes = pack_header(header)
    return header_bytes + ciphertext


def unpack_envelope(data: bytes) -> EncryptedEnvelope:
    """Unpacks full encrypted envelope and validates total length."""
    header, header_bytes = unpack_header(data)
    expected_total = HEADER_SIZE + header.ciphertext_length
    if len(data) < expected_total:
        raise CorruptedPayloadError(
            f"Incomplete payload: received {len(data)} bytes, expected {expected_total} bytes."
        )
    ciphertext = data[HEADER_SIZE:expected_total]
    return EncryptedEnvelope(
        header=header,
        header_bytes=header_bytes,
        ciphertext=ciphertext,
    )
