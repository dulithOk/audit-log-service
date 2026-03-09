import logging
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Paths that bypass API key auth
EXEMPT_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi",
    "/health",
    "/metrics",
    "/favicon.ico",
)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        # Skip auth if no keys are configured (open mode — dev only)
        if not settings.api_key_list:
            return await call_next(request)
        api_key = request.headers.get(settings.api_key_header)
        if not api_key or api_key not in settings.api_key_list:
            logger.warning(
                "Unauthorized request",
                extra={"path": request.url.path, "ip": request.client.host},
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)
