"""Password-based key derivation using Argon2id.

Follows RFC 9106 standards for high-security password hashing and derivation.
Uses cryptographically secure random salts and memory-hard parameters to resist ASIC/GPU attacks.
"""

import os
from typing import Optional
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from app.core.config import settings
from app.crypto.models import KdfParameters


def generate_salt(length: int = 16) -> bytes:
    """Generates a cryptographically secure random salt."""
    return os.urandom(length)


def derive_key(
    password: str,
    salt: bytes,
    time_cost: Optional[int] = None,
    memory_cost: Optional[int] = None,
    parallelism: Optional[int] = None,
    key_length: int = 32,
) -> bytes:
    """Derives a 256-bit symmetric key from password and salt using Argon2id.

    Args:
        password: Plaintext password provided by user.
        salt: Random 16-byte salt.
        time_cost: Number of iterations (Argon2 time cost).
        memory_cost: Memory consumption in KiB (e.g. 65536 = 64 MiB).
        parallelism: Number of parallel lanes.
        key_length: Length of derived key in bytes (default 32 bytes = 256 bits).

    Returns:
        32-byte derived symmetric key.
    """
    iterations = time_cost if time_cost is not None else settings.ARGON2_TIME_COST
    mem = memory_cost if memory_cost is not None else settings.ARGON2_MEMORY_COST
    lanes = parallelism if parallelism is not None else settings.ARGON2_PARALLELISM

    password_bytes = password.encode("utf-8") if isinstance(password, str) else password

    kdf = Argon2id(
        salt=salt,
        length=key_length,
        iterations=iterations,
        lanes=lanes,
        memory_cost=mem,
    )
    return kdf.derive(password_bytes)


def get_default_kdf_params() -> KdfParameters:
    """Returns default KDF parameters with a fresh secure salt."""
    return KdfParameters(
        time_cost=settings.ARGON2_TIME_COST,
        memory_cost=settings.ARGON2_MEMORY_COST,
        parallelism=settings.ARGON2_PARALLELISM,
        salt=generate_salt(settings.ARGON2_SALT_BYTES),
    )
