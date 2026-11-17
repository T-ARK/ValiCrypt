"""Common schemas and response models for MediaVault."""

from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully."


class GenericResponse(BaseResponse, Generic[DataT]):
    data: Optional[DataT] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
