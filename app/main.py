import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.database import engine
from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.controller.audit_log_controller import router as audit_log_router
from app.exceptions.errors import DatabaseError, NotFoundError, UnauthorizedError
from app.middleware.auth import APIKeyMiddleware
from app.middleware.request_id import RequestIDMiddleware

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Audit Log Service",
        description=(
            "A reusable, production-grade audit logging service. "
            "Integrate via API key from any internal service."
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        openapi_url="/openapi.json" if settings.app_env != "production" else None,
    )

    # Middleware — order matters (outermost applied last)
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(audit_log_router, prefix="/api/v1")

    # Exception handlers
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        logger.error("Database error", extra={"detail": exc.detail})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "A database error occurred. Please try again."},
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
        )

    @app.get("/health", tags=["Health"])
    async def health_check():
        try:
            async with engine.connect():
                pass
            db_status = "ok"
        except Exception:
            db_status = "unreachable"

        return {
            "status": "ok" if db_status == "ok" else "degraded",
            "version": settings.app_version,
            "db": db_status,
        }

    @app.on_event("startup")
    async def on_startup():
        logger.info("Audit Log Service starting up", extra={"env": settings.app_env})

    @app.on_event("shutdown")
    async def on_shutdown():
        await engine.dispose()
        logger.info("Audit Log Service shut down cleanly")

    return app


app = create_app()
