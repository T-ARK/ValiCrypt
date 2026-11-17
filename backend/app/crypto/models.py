"""Cryptographic models and enumerations for MediaVault."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class PayloadType(IntEnum):
    TEXT = 1
    ZIP = 2
    BINARY = 3

    @classmethod
    def from_str(cls, val: str) -> "PayloadType":
        lower = val.lower()
        if lower in ("text", "txt"):
            return cls.TEXT
        if lower in ("zip", "archive"):
            return cls.ZIP
        return cls.BINARY


class CryptoAlgorithm(IntEnum):
    AES_256_GCM = 1


class KdfAlgorithm(IntEnum):
    ARGON2ID = 1


@dataclass(frozen=True)
class KdfParameters:
    time_cost: int
    memory_cost: int  # in KiB
    parallelism: int
    salt: bytes


@dataclass
class EnvelopeHeader:
    magic: bytes  # b"MV01"
    version: int  # 1
    algorithm: CryptoAlgorithm  # AES_256_GCM
    kdf: KdfAlgorithm  # ARGON2ID
    payload_type: PayloadType  # TEXT / ZIP / BINARY
    time_cost: int
    memory_cost: int
    parallelism: int
    salt: bytes  # 16 bytes
    nonce: bytes  # 12 bytes
    plaintext_length: int  # 8 bytes
    ciphertext_length: int  # 4 bytes
    plaintext_sha256: bytes  # 32 bytes


@dataclass
class EncryptedEnvelope:
    header: EnvelopeHeader
    header_bytes: bytes
    ciphertext: bytes  # Includes 16-byte GCM authentication tag


@dataclass
class DecryptedPayload:
    payload_type: PayloadType
    data: bytes
    plaintext_sha256: str
