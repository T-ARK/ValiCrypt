"""Comprehensive unit tests for the cryptographic engine.

Tests:
  - Encryption and decryption roundtrip
  - Incorrect password safe failure
  - Ciphertext tampering detection
  - Auth tag tampering detection
  - Header/AAD tampering detection
  - Nonce uniqueness across invocations
  - Salt uniqueness across invocations
  - Multilingual Unicode text handling (Malayalam, Hindi, Emoji, symbols)
  - Empty message handling
  - Large payload roundtrip
"""

import hashlib
import pytest
from app.core.errors import (
    CorruptedPayloadError,
    DecryptionError,
    EncryptionError,
    InvalidPasswordError,
)
from app.crypto.encryption import decrypt_payload, encrypt_payload
from app.crypto.envelope import unpack_header
from app.crypto.models import PayloadType


def test_encryption_decryption_roundtrip_text():
    """Verify standard text roundtrip with correct password."""
    secret = "Hello from MediaVault! 12345"
    password = "SuperSecurePassword#2026!"
    
    envelope = encrypt_payload(secret.encode("utf-8"), password, PayloadType.TEXT)
    decrypted = decrypt_payload(envelope, password)
    
    assert decrypted.payload_type == PayloadType.TEXT
    assert decrypted.data.decode("utf-8") == secret
    assert decrypted.plaintext_sha256 == hashlib.sha256(secret.encode("utf-8")).hexdigest()


def test_wrong_password_fails_safely():
    """Verify wrong password fails with InvalidPasswordError without leaking details."""
    secret = "Top Secret Information"
    password = "CorrectPassword123"
    wrong_password = "WrongPassword999"
    
    envelope = encrypt_payload(secret.encode("utf-8"), password, PayloadType.TEXT)
    
    with pytest.raises(InvalidPasswordError) as exc_info:
        decrypt_payload(envelope, wrong_password)
    assert "Decryption failed" in str(exc_info.value)


def test_modified_ciphertext_fails():
    """Tampering with a single bit in the ciphertext must trigger an integrity failure."""
    secret = "Sensitive payload data"
    password = "MyPassword123"
    
    envelope = bytearray(encrypt_payload(secret.encode("utf-8"), password, PayloadType.TEXT))
    
    # Tamper with the last byte of ciphertext/tag
    envelope[-1] ^= 0x01
    
    with pytest.raises(InvalidPasswordError):
        decrypt_payload(bytes(envelope), password)


def test_modified_auth_tag_fails():
    """Tampering with the authentication tag must trigger an integrity failure."""
    secret = "Confidential business contract"
    password = "ContractPassword2026"
    
    envelope = bytearray(encrypt_payload(secret.encode("utf-8"), password, PayloadType.TEXT))
    
    # Tamper with byte in the auth tag region (last 16 bytes)
    envelope[-8] ^= 0x55
    
    with pytest.raises(InvalidPasswordError):
        decrypt_payload(bytes(envelope), password)


def test_modified_header_aad_fails():
    """Tampering with envelope header fields must fail because header is bound in AES-GCM AAD."""
    secret = "Confidential records"
    password = "SafePassword"
    
    envelope = bytearray(encrypt_payload(secret.encode("utf-8"), password, PayloadType.TEXT))
    
    # Header byte 7 is PayloadType (offset 7)
    envelope[7] = 2 if envelope[7] == 1 else 1
    
    with pytest.raises((InvalidPasswordError, CorruptedPayloadError)):
        decrypt_payload(bytes(envelope), password)


def test_unique_salt_and_nonce():
    """Consecutive encryptions of the same data and password must yield distinct salts and nonces."""
    data = b"Repeated data payload"
    password = "IdenticalPassword"
    
    env1 = encrypt_payload(data, password, PayloadType.BINARY)
    env2 = encrypt_payload(data, password, PayloadType.BINARY)
    
    header1, _ = unpack_header(env1)
    header2, _ = unpack_header(env2)
    
    assert header1.salt != header2.salt
    assert header1.nonce != header2.nonce
    assert env1 != env2


def test_multilingual_unicode_support():
    """Verify full Unicode support: English, Malayalam, Hindi, emojis, symbols, numbers."""
    multilingual_text = (
        "English: Hello World 2026!\n"
        "Malayalam: മീഡിയവോൾട്ട് രഹസ്യ വിവര ശേഖരണം സ്വാഗതം\n"
        "Hindi: मीडियावॉल्ट सुरक्षित एन्क्रिप्शन प्रणाली\n"
        "Symbols & Numbers: π ≈ 3.1415926535, €100, $500, ±0.05, © 2026\n"
        "Emojis: 🔐🚀🛡️✨💻📦🎉"
    )
    password = "ക്രിപ്റ്റോഗ്രഫി@123_ताला_🔑"
    
    data = multilingual_text.encode("utf-8")
    envelope = encrypt_payload(data, password, PayloadType.TEXT)
    decrypted = decrypt_payload(envelope, password)
    
    assert decrypted.data.decode("utf-8") == multilingual_text
    assert decrypted.payload_type == PayloadType.TEXT


def test_empty_message_handling():
    """Empty payload must encrypt and decrypt correctly."""
    empty_data = b""
    password = "PasswordForEmpty"
    
    envelope = encrypt_payload(empty_data, password, PayloadType.TEXT)
    decrypted = decrypt_payload(envelope, password)
    
    assert decrypted.data == b""
    assert decrypted.plaintext_sha256 == hashlib.sha256(b"").hexdigest()


def test_empty_password_fails():
    """Empty password must be rejected during encryption and decryption."""
    data = b"Some data"
    with pytest.raises(EncryptionError):
        encrypt_payload(data, "", PayloadType.TEXT)
        
    envelope = encrypt_payload(data, "ValidPassword", PayloadType.TEXT)
    with pytest.raises(InvalidPasswordError):
        decrypt_payload(envelope, "")


def test_large_payload_roundtrip():
    """Verify encryption and decryption for a large payload (1 MB)."""
    large_data = b"A" * (1024 * 1024)
    password = "LargeDataPassword"
    
    envelope = encrypt_payload(large_data, password, PayloadType.ZIP)
    decrypted = decrypt_payload(envelope, password)
    
    assert len(decrypted.data) == 1024 * 1024
    assert decrypted.data == large_data
    assert decrypted.payload_type == PayloadType.ZIP
