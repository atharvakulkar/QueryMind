"""Request and response models for every public route."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Structured error payload returned to clients."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Top-level error envelope."""

    error: ErrorBody


class HealthResponse(BaseModel):
    """Process liveness."""

    status: str = "ok"
    app_name: str


class ReadyResponse(BaseModel):
    """Readiness including database connectivity."""

    status: str
    database_reachable: bool


class DemoDatasetResponse(BaseModel):
    """Result of a fixed, safe demo query (no user SQL)."""

    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float


class SqlExecuteRequest(BaseModel):
    """Optional dev-only ad-hoc read SQL."""

    sql: str = Field(min_length=1, max_length=20_000)


class SqlExecuteResponse(BaseModel):
    """Tabular result with timing metadata."""

    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float
