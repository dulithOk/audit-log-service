from typing import Any, Dict, Optional


class AuditLogServiceError(Exception):
    """Base exception for this service."""

    def __init__(self, message: str, detail: Optional[Any] = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(AuditLogServiceError):
    pass


class ValidationError(AuditLogServiceError):
    pass


class DatabaseError(AuditLogServiceError):
    pass


class UnauthorizedError(AuditLogServiceError):
    pass
