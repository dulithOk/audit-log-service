import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Who performed the action
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(100), nullable=False)  # user, service, system
    actor_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # What was done
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # success, failure, error

    # On which resource
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Originating service — enables multi-service integration
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    service_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Request tracing
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Payload snapshots — nullable to support lightweight events
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Human-readable description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_audit_logs_service_action", "service_name", "action"),
        Index("ix_audit_logs_actor_created", "actor_id", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_created_at_desc", created_at.desc()),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"actor={self.actor_id} service={self.service_name}>"
        )
