"""Liveness and readiness endpoints."""

import logging

from fastapi import APIRouter, status

from backend.dependencies import ConnectionManagerDep, SettingsDep
from backend.schemas.api import HealthResponse, ReadyResponse
from core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDep) -> HealthResponse:
    """Liveness probe; does not check the database."""
    return HealthResponse(status="ok", app_name=settings.app_name)


@router.get("/ready", response_model=ReadyResponse)
async def ready(connection_manager: ConnectionManagerDep) -> ReadyResponse:
    """Readiness probe; verifies the database pool."""
    ok = await connection_manager.health_check()
    if not ok:
        logger.warning("Readiness check failed: database not reachable.")
        raise DatabaseConnectionError(
            "Database is not reachable.",
            details={"hint": "Verify DATABASE_URL and DB availability."},
        )
    return ReadyResponse(status="ready", database_reachable=True)
