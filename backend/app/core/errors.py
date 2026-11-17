"""Structured error definitions for MediaVault.

Every error includes an unambiguous error code, user-friendly message, and HTTP status.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class MediaVaultError(HTTPException):
    """Base exception for all structured MediaVault errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": self.details,
            },
        )


class InvalidFileError(MediaVaultError):
    def __init__(self, message: str = "Invalid or unreadable file provided.", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="INVALID_FILE", message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class UnsupportedFormatError(MediaVaultError):
    def __init__(self, message: str = "File format is not supported.", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="UNSUPPORTED_FORMAT", message=message, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, details=details)


class InsufficientCapacityError(MediaVaultError):
    def __init__(
        self,
        available_bytes: int,
        required_bytes: int,
        message: Optional[str] = None,
    ):
        msg = message or f"Carrier capacity ({available_bytes} bytes) is insufficient for payload ({required_bytes} bytes)."
        super().__init__(
            code="INSUFFICIENT_CAPACITY",
            message=msg,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"available_bytes": available_bytes, "required_bytes": required_bytes},
        )


class InvalidPasswordError(MediaVaultError):
    def __init__(self, message: str = "Decryption failed. The provided password is invalid or the data is corrupted."):
        super().__init__(
            code="INVALID_PASSWORD",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class CorruptedPayloadError(MediaVaultError):
    def __init__(self, message: str = "Integrity verification failed. Carrier or payload has been tampered with or corrupted."):
        super().__init__(
            code="CORRUPTED_PAYLOAD",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if hasattr(status, "HTTP_422_UNPROCESSABLE_ENTITY") else 422,
        )


class InvalidPayloadError(MediaVaultError):
    def __init__(self, message: str = "The payload data is malformed or invalid.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="INVALID_PAYLOAD",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class VideoProcessingError(MediaVaultError):
    def __init__(self, message: str = "Video processing or transcoding failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="VIDEO_PROCESSING_FAILED",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class EncryptionError(MediaVaultError):
    def __init__(self, message: str = "Encryption operation failed."):
        super().__init__(
            code="ENCRYPTION_FAILED",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class DecryptionError(MediaVaultError):
    def __init__(self, message: str = "Decryption failed."):
        super().__init__(
            code="DECRYPTION_FAILED",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class OversizedUploadError(MediaVaultError):
    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(
            code="OVERSIZED_UPLOAD",
            message=f"Upload size ({size_bytes} bytes) exceeds maximum allowed limit ({max_bytes} bytes).",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"size_bytes": size_bytes, "max_bytes": max_bytes},
        )


class SecurityViolationError(MediaVaultError):
    def __init__(self, message: str = "Security violation detected."):
        super().__init__(
            code="SECURITY_VIOLATION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class JobNotFoundError(MediaVaultError):
    def __init__(self, job_id: str):
        super().__init__(
            code="JOB_NOT_FOUND",
            message=f"Job with ID '{job_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"job_id": job_id},
        )
