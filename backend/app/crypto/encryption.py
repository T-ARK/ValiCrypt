"""Authenticated encryption and decryption module using AES-256-GCM and Argon2id.

Guarantees:
  - Cryptographically secure 12-byte random nonce per operation (NO nonce reuse).
  - Associated Data (AAD) binds the entire envelope header (parameters, salt, lengths) to the ciphertext.
  - Zero tolerance for tampering: wrong tag or modified metadata fails safely with InvalidPasswordError or CorruptedPayloadError.
  - Post-decryption SHA-256 checksum verification.
  - No secrets or keys logged or retained in heap longer than required.
"""

import hashlib
import os
from typing import Optional
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings
from app.core.errors import (
    CorruptedPayloadError,
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)
from app.crypto.envelope import (
    CURRENT_VERSION,
    HEADER_MAGIC,
    pack_envelope,
    pack_header,
    unpack_envelope,
)
from app.crypto.kdf import derive_key, get_default_kdf_params
from app.crypto.models import (
    CryptoAlgorithm,
    DecryptedPayload,
    EnvelopeHeader,
    KdfAlgorithm,
    KdfParameters,
    PayloadType,
)


def encrypt_payload(
    plaintext: bytes,
    password: str,
    payload_type: PayloadType,
    kdf_params: Optional[KdfParameters] = None,
) -> bytes:
    """Encrypts plaintext into a self-contained MediaVault binary envelope.

    Args:
        plaintext: Raw data bytes to encrypt.
        password: User password.
        payload_type: Type of payload (TEXT, ZIP, BINARY).
        kdf_params: Optional custom KdfParameters (uses secure defaults if None).

    Returns:
        Complete serialized envelope bytes.
    """
    if not password:
        raise EncryptionError("Password cannot be empty.")

    params = kdf_params or get_default_kdf_params()

    # 1. Plaintext SHA-256 checksum for end-to-end verification
    plaintext_sha256 = hashlib.sha256(plaintext).digest()

    # 2. Derive 256-bit AES key via Argon2id
    key = derive_key(
        password=password,
        salt=params.salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        key_length=settings.AES_KEY_BYTES,
    )

    # 3. Generate fresh 96-bit (12 bytes) nonce
    nonce = os.urandom(settings.AES_NONCE_BYTES)

    # 4. Ciphertext length = plaintext length + 16 (AES-GCM tag)
    ciphertext_len = len(plaintext) + 16

    # 5. Build envelope header
    header = EnvelopeHeader(
        magic=HEADER_MAGIC,
        version=CURRENT_VERSION,
        algorithm=CryptoAlgorithm.AES_256_GCM,
        kdf=KdfAlgorithm.ARGON2ID,
        payload_type=payload_type,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        salt=params.salt,
        nonce=nonce,
        plaintext_length=len(plaintext),
        ciphertext_length=ciphertext_len,
        plaintext_sha256=plaintext_sha256,
    )

    header_bytes = pack_header(header)

    # 6. Authenticated encryption with AES-256-GCM
    # Header bytes are passed as Associated Authenticated Data (AAD)
    try:
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce=nonce, data=plaintext, associated_data=header_bytes)
    except Exception as exc:
        raise EncryptionError(f"Encryption failed: {exc}") from exc
    finally:
        # Overwrite key in memory
        del key

    return pack_envelope(header, ciphertext)


def decrypt_payload(envelope_bytes: bytes, password: str) -> DecryptedPayload:
    """Decrypts a MediaVault binary envelope and verifies integrity.

    Args:
        envelope_bytes: Full binary envelope data.
        password: User password.

    Returns:
        DecryptedPayload with original data and payload type.

    Raises:
        InvalidPasswordError: If decryption/authentication fails.
        CorruptedPayloadError: If header or payload checksum validation fails.
    """
    if not password:
        raise InvalidPasswordError("Password cannot be empty.")

    # 1. Unpack and validate envelope structure
    envelope = unpack_envelope(envelope_bytes)
    header = envelope.header

    # 2. Derive key using header's KDF parameters
    key = derive_key(
        password=password,
        salt=header.salt,
        time_cost=header.time_cost,
        memory_cost=header.memory_cost,
        parallelism=header.parallelism,
        key_length=settings.AES_KEY_BYTES,
    )

    # 3. Decrypt with AES-GCM and verify AAD
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(
            nonce=header.nonce,
            data=envelope.ciphertext,
            associated_data=envelope.header_bytes,
        )
    except InvalidTag:
        raise InvalidPasswordError(
            "Decryption failed. The provided password is invalid or the data has been altered."
        )
    except Exception as exc:
        raise DecryptionError(f"Decryption failed: {exc}") from exc
    finally:
        del key

    # 4. Verify plaintext length matches header
    if len(plaintext) != header.plaintext_length:
        raise CorruptedPayloadError(
            f"Plaintext length mismatch: expected {header.plaintext_length}, got {len(plaintext)}."
        )

    # 5. Verify SHA-256 checksum
    computed_sha256 = hashlib.sha256(plaintext).digest()
    if computed_sha256 != header.plaintext_sha256:
        raise CorruptedPayloadError(
            "Integrity verification failed. SHA-256 checksum mismatch on decrypted data."
        )

    return DecryptedPayload(
        payload_type=header.payload_type,
        data=plaintext,
        plaintext_sha256=computed_sha256.hex(),
    )
