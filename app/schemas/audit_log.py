import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditLogCreate(BaseModel):
    actor_id: str = Field(..., max_length=255)
    actor_type: str = Field(..., max_length=100)
    actor_ip: Optional[str] = Field(None, max_length=45)

    action: str = Field(..., max_length=255)
    status: str = Field(..., max_length=50)

    resource_type: str = Field(..., max_length=255)
    resource_id: Optional[str] = Field(None, max_length=255)

    service_name: str = Field(..., max_length=255)
    service_version: Optional[str] = Field(None, max_length=50)

    trace_id: Optional[str] = Field(None, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)

    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"success", "failure", "error"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: str
    actor_type: str
    actor_ip: Optional[str]

    action: str
    status: str

    resource_type: str
    resource_id: Optional[str]

    service_name: str
    service_version: Optional[str]

    trace_id: Optional[str]
    session_id: Optional[str]

    before_state: Optional[Dict[str, Any]]
    after_state: Optional[Dict[str, Any]]
    meta_data: Optional[Dict[str, Any]]
    description: Optional[str]

    created_at: datetime


class AuditLogFilter(BaseModel):
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    service_name: Optional[str] = None
    trace_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class PaginatedResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BulkCreateRequest(BaseModel):
    logs: List[AuditLogCreate] = Field(..., min_length=1, max_length=1000)


class BulkCreateResponse(BaseModel):
    created: int
    ids: List[uuid.UUID]


class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
