"""Pydantic schemas for encoding, decoding, verification, capacity, and jobs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.db.models import JobOperation, JobStatus


# Capacity Schemas
class CapacityRequest(BaseModel):
    carrier_type: str  # "image" or "video"
    width: Optional[int] = None
    height: Optional[int] = None
    channels: Optional[int] = 3


class CapacityResponse(BaseModel):
    carrier_type: str
    carrier_size_bytes: int
    available_capacity_bytes: int
    available_capacity_human: str
    sufficient: bool = True
    carrier_info: Dict[str, Any] = Field(default_factory=dict)


# Encode Response Schemas
class EncodeSyncResponse(BaseModel):
    success: bool = True
    job_id: str
    download_url: str
    filename: str
    mime_type: str
    carrier_type: str
    payload_type: str
    output_size_bytes: int
    sha256_checksum: str


# Decode Response Schemas
class DecodeResponse(BaseModel):
    success: bool = True
    payload_type: str  # "TEXT" or "ZIP"
    text_content: Optional[str] = None
    download_url: Optional[str] = None
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    sha256_checksum: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Verify Schemas
class VerifyResponse(BaseModel):
    carrier_type: str
    media_format: str
    mediavault_version: Optional[int] = None
    payload_present: bool
    payload_type: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    kdf_algorithm: Optional[str] = None
    payload_size_bytes: Optional[int] = None
    integrity_status: str  # "VALID", "NOT_DETECTED", "CORRUPTED"
    carrier_properties: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = (
        "Technical verification inspects structural MediaVault preambles. "
        "It does not guarantee unobservability against statistical steganalysis."
    )


# Job Schemas
class JobResponse(BaseModel):
    id: str
    status: JobStatus
    operation: JobOperation
    carrier_type: str
    payload_type: Optional[str] = None
    carrier_size: int
    payload_size: Optional[int] = None
    progress: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
