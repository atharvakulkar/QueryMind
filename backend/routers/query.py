"""Read-only data routes (demo and optional gated ad-hoc SQL)."""

import logging

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder

from backend.dependencies import ConnectionManagerDep, SettingsDep
from backend.schemas.api import DemoDatasetResponse, SqlExecuteRequest, SqlExecuteResponse
from core.exceptions import SQLExecutionError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


_DEMO_SQL = """
SELECT current_database() AS database, now() AS server_time;
"""


@router.get("/demo/dataset", response_model=DemoDatasetResponse)
async def demo_dataset(connection_manager: ConnectionManagerDep) -> DemoDatasetResponse:
    """Run a fixed, safe query to verify connectivity without user-provided SQL."""
    columns, rows, elapsed = await connection_manager.fetch_all(
        _DEMO_SQL,
        enforce_guard=False,
    )
    safe_rows = [jsonable_encoder(row) for row in rows]
    logger.info("Demo dataset served in %.3f ms.", elapsed * 1000)
    return DemoDatasetResponse(
        columns=columns,
        rows=safe_rows,
        execution_time_ms=round(elapsed * 1000, 3),
    )


@router.post(
    "/internal/execute-read",
    response_model=SqlExecuteResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_read(
    body: SqlExecuteRequest,
    connection_manager: ConnectionManagerDep,
    settings: SettingsDep,
) -> SqlExecuteResponse:
    """
    Developer-only endpoint for ad-hoc SELECT queries.

    Disabled unless ALLOW_ADHOC_SQL=true in the environment.
    """
    if not settings.allow_adhoc_sql:
        raise SQLExecutionError(
            "Ad-hoc SQL execution is disabled.",
            code="adhoc_sql_disabled",
            details={"hint": "Set ALLOW_ADHOC_SQL=true for local development only."},
        )

    columns, rows, elapsed = await connection_manager.fetch_all(body.sql, enforce_guard=True)
    safe_rows = [jsonable_encoder(row) for row in rows]
    logger.warning("Ad-hoc SQL executed (ALLOW_ADHOC_SQL enabled).")
    return SqlExecuteResponse(
        columns=columns,
        rows=safe_rows,
        execution_time_ms=round(elapsed * 1000, 3),
    )
