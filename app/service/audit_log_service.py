import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogResponse,
    BulkCreateRequest,
    BulkCreateResponse,
    PaginatedResponse,
)


class AuditLogService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditLogRepository(db)

    async def create_log(self, data: AuditLogCreate) -> AuditLogResponse:
        log = await self._repo.create(data)
        return AuditLogResponse.model_validate(log)

    async def bulk_create_logs(
        self, request: BulkCreateRequest
    ) -> BulkCreateResponse:
        logs = await self._repo.bulk_create(request.logs)
        return BulkCreateResponse(created=len(logs), ids=[log.id for log in logs])

    async def get_log(self, log_id: uuid.UUID) -> AuditLogResponse:
        log = await self._repo.get_by_id(log_id)
        return AuditLogResponse.model_validate(log)

    async def list_logs(self, filters: AuditLogFilter) -> PaginatedResponse:
        logs, total = await self._repo.list_with_filters(filters)
        pages = math.ceil(total / filters.page_size) if total > 0 else 0
        return PaginatedResponse(
            items=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )
