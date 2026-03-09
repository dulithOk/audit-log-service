import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import DatabaseError, NotFoundError
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogFilter


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: AuditLogCreate) -> AuditLog:
        try:
            log = AuditLog(**data.model_dump())
            self._db.add(log)
            await self._db.flush()
            await self._db.refresh(log)
            return log
        except Exception as exc:
            raise DatabaseError("Failed to create audit log", detail=str(exc)) from exc

    async def bulk_create(self, items: List[AuditLogCreate]) -> List[AuditLog]:
        try:
            logs = [AuditLog(**item.model_dump()) for item in items]
            self._db.add_all(logs)
            await self._db.flush()
            for log in logs:
                await self._db.refresh(log)
            return logs
        except Exception as exc:
            raise DatabaseError("Failed to bulk create audit logs", detail=str(exc)) from exc

    async def get_by_id(self, log_id: uuid.UUID) -> AuditLog:
        result = await self._db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            raise NotFoundError(f"Audit log {log_id} not found")
        return log

    async def list_with_filters(
        self, filters: AuditLogFilter
    ) -> Tuple[List[AuditLog], int]:
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        query, count_query = self._apply_filters(query, count_query, filters)

        # Total count
        total_result = await self._db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results — newest first
        offset = (filters.page - 1) * filters.page_size
        query = (
            query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )

        result = await self._db.execute(query)
        return result.scalars().all(), total

    def _apply_filters(self, query, count_query, filters: AuditLogFilter):
        conditions = []

        if filters.actor_id:
            conditions.append(AuditLog.actor_id == filters.actor_id)
        if filters.actor_type:
            conditions.append(AuditLog.actor_type == filters.actor_type)
        if filters.action:
            conditions.append(AuditLog.action == filters.action)
        if filters.status:
            conditions.append(AuditLog.status == filters.status)
        if filters.resource_type:
            conditions.append(AuditLog.resource_type == filters.resource_type)
        if filters.resource_id:
            conditions.append(AuditLog.resource_id == filters.resource_id)
        if filters.service_name:
            conditions.append(AuditLog.service_name == filters.service_name)
        if filters.trace_id:
            conditions.append(AuditLog.trace_id == filters.trace_id)
        if filters.date_from:
            conditions.append(AuditLog.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(AuditLog.created_at <= filters.date_to)

        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)

        return query, count_query
