import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.params import Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogResponse,
    BulkCreateRequest,
    BulkCreateResponse,
    PaginatedResponse,
)
from app.service.audit_log_service import AuditLogService

api_key_header = APIKeyHeader(name='Authorization')
router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def get_service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    return AuditLogService(db)


@router.post(
    "/",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single audit log entry",
)
async def create_audit_log(
    body: AuditLogCreate,
    service: AuditLogService = Depends(get_service),
    api_key: str = Security(api_key_header),
) -> AuditLogResponse:
    return await service.create_log(body)


@router.post(
    "/bulk",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk-create audit log entries (max 1000 per request)",
)
async def bulk_create_audit_logs(
    body: BulkCreateRequest,
    service: AuditLogService = Depends(get_service),
    api_key: str = Security(api_key_header),
) -> BulkCreateResponse:
    return await service.bulk_create_logs(body)


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List and filter audit logs",
)
async def list_audit_logs(
    actor_id: Optional[str] = Query(None),
    actor_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    trace_id: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    service: AuditLogService = Depends(get_service),
    api_key: str = Security(api_key_header),
) -> PaginatedResponse:
    filters = AuditLogFilter(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        status=status,
        resource_type=resource_type,
        resource_id=resource_id,
        service_name=service_name,
        trace_id=trace_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return await service.list_logs(filters)


@router.get(
    "/{log_id}",
    response_model=AuditLogResponse,
    summary="Get a single audit log entry by ID",
)
async def get_audit_log(
    log_id: uuid.UUID,
    service: AuditLogService = Depends(get_service),
    api_key: str = Security(api_key_header),
) -> AuditLogResponse:
    return await service.get_log(log_id)
