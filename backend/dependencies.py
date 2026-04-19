"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from core.config import Settings
from database.connection_manager import ConnectionManager


def get_app_settings(request: Request) -> Settings:
    """Return Settings bound at application startup."""
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application settings are not initialized.",
        )
    return settings


def get_connection_manager(request: Request) -> ConnectionManager:
    """Return the shared ConnectionManager from app state."""
    cm = getattr(request.app.state, "connection_manager", None)
    if cm is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection manager is not available.",
        )
    return cm


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
ConnectionManagerDep = Annotated[ConnectionManager, Depends(get_connection_manager)]
