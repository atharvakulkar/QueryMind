"""FastAPI application entry and factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import agent, health, query
from backend.schemas.api import ErrorBody, ErrorResponse
from core.config import Settings, get_settings
from core.exceptions import (
    ConfigError,
    DatabaseConnectionError,
    MCPConnectionError,
    QueryMindError,
    SQLExecutionError,
    SQLGenerationError,
    SchemaLinkingError,
)
from core.logging_config import configure_logging
from database.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


def create_app(
    *,
    settings: Settings | None = None,
    connection_manager: ConnectionManager | None = None,
) -> FastAPI:
    """
    Build the FastAPI application.

    Parameters
    ----------
    settings:
        Optional settings override (used by tests).
    connection_manager:
        Optional pre-built manager (skips connect/close lifecycle when provided).
    """
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(resolved_settings.log_level)
        app.state.settings = resolved_settings
        if connection_manager is not None:
            app.state.connection_manager = connection_manager
            app.state._querymind_own_pool = False
        else:
            cm = ConnectionManager(resolved_settings)
            await cm.connect()
            app.state.connection_manager = cm
            app.state._querymind_own_pool = True
        try:
            yield
        finally:
            if getattr(app.state, "_querymind_own_pool", False):
                try:
                    await app.state.connection_manager.close()
                except Exception:  # pragma: no cover - defensive shutdown
                    logger.exception("Error while closing database pool.")

    app = FastAPI(
        lifespan=lifespan,
        title=resolved_settings.app_name,
        version="0.1.0",
        description="QueryMind API — read-only PostgreSQL, MCP schema tools, NL→SQL agent.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:5173",   # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:8501",   # Streamlit (Phase 4 legacy)
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(QueryMindError)
    async def _querymind_error_handler(
        request: Request,
        exc: QueryMindError,
    ) -> JSONResponse:
        if isinstance(exc, DatabaseConnectionError):
            code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(exc, MCPConnectionError):
            code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(exc, ConfigError):
            code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, SchemaLinkingError):
            code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, SQLGenerationError):
            code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, SQLExecutionError):
            code = status.HTTP_400_BAD_REQUEST
        else:
            code = status.HTTP_400_BAD_REQUEST
        payload = ErrorResponse(
            error=ErrorBody(code=exc.code, message=exc.message, details=exc.details),
        )
        return JSONResponse(status_code=code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled exception during request processing.")
        payload = ErrorResponse(
            error=ErrorBody(
                code="internal_error",
                message="An unexpected error occurred.",
                details={},
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )

    app.include_router(health.router)
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(agent.router, prefix="/api/v1")

    # --- Serve compiled Vite frontend when available (Docker / production) ---
    _dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if _dist.is_dir():
        _index = _dist / "index.html"

        # Serve static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="static-assets")

        # SPA catch-all: any non-API path serves index.html
        @app.get("/{full_path:path}", include_in_schema=False)
        async def _spa_fallback(full_path: str) -> FileResponse:
            # Serve the file directly if it exists in dist (e.g. favicon.ico)
            candidate = _dist / full_path
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(_index))

        logger.info("Serving compiled frontend from %s", _dist)

    return app
