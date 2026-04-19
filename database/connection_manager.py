"""Async PostgreSQL pool with read-oriented guards and timing logs."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import asyncpg

from core.config import Settings
from core.exceptions import DatabaseConnectionError, SQLExecutionError

logger = logging.getLogger(__name__)

# Best-effort guard only; database role must be read-only in production.
_FORBIDDEN_LEADING = (
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "CALL",
    "EXECUTE",
)


def assert_read_only_select_sql(sql: str) -> None:
    """Reject obviously mutating or non-SELECT statements (best-effort)."""
    stripped = sql.strip()
    if not stripped:
        raise SQLExecutionError("Empty SQL is not allowed.", code="sql_not_allowed")
    upper = stripped.upper()
    token = upper.split(None, 1)[0] if upper else ""
    if token in _FORBIDDEN_LEADING:
        raise SQLExecutionError(
            f"Statements starting with {token} are not allowed.",
            code="sql_not_allowed",
        )
    if token not in ("SELECT", "WITH"):
        raise SQLExecutionError(
            "Only SELECT or WITH queries are allowed.",
            code="sql_not_allowed",
        )
    if re.search(r";\s*\S", stripped):
        raise SQLExecutionError(
            "Chained statements (multiple statements) are not allowed.",
            code="sql_not_allowed",
        )


class ConnectionManager:
    """Owns asyncpg pool lifecycle and safe read queries."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise DatabaseConnectionError("Database pool is not initialized.")
        return self._pool

    async def connect(self) -> None:
        """Create the connection pool."""
        timeout_ms = int(self._settings.statement_timeout_seconds * 1000)

        async def _init_connection(conn: asyncpg.Connection) -> None:
            await conn.execute(f"SET statement_timeout = {timeout_ms}")

        try:
            self._pool = await asyncpg.create_pool(
                dsn=str(self._settings.database_url),
                min_size=1,
                max_size=10,
                command_timeout=float(self._settings.statement_timeout_seconds),
                init=_init_connection,
            )
            logger.info("Database pool connected.")
        except Exception as exc:
            logger.exception("Failed to connect to PostgreSQL.")
            raise DatabaseConnectionError(
                "Could not connect to the database.",
                details={"reason": str(exc)},
            ) from exc

    async def close(self) -> None:
        """Close pool if present."""
        if self._pool is not None:
            try:
                await self._pool.close()
                logger.info("Database pool closed.")
            finally:
                self._pool = None

    async def health_check(self) -> bool:
        """Return True if a simple query succeeds."""
        try:
            async with self.pool.acquire() as conn:
                val = await conn.fetchval("SELECT 1")
            return val == 1
        except Exception:
            logger.exception("Database health check failed.")
            return False

    async def fetch_all(
        self,
        sql: str,
        *,
        params: tuple[Any, ...] | list[Any] | None = None,
        enforce_guard: bool = True,
    ) -> tuple[list[str], list[dict[str, Any]], float]:
        """
        Execute a read query and return columns, row dicts, and elapsed seconds.

        Rows are capped at settings.max_query_rows.
        """
        if enforce_guard:
            assert_read_only_select_sql(sql)

        params = params or ()
        start = time.perf_counter()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
        except SQLExecutionError:
            raise
        except Exception as exc:
            logger.exception("SQL execution failed.")
            raise SQLExecutionError(
                "Query execution failed.",
                details={"reason": str(exc)},
            ) from exc
        elapsed = time.perf_counter() - start

        max_rows = self._settings.max_query_rows
        trimmed = rows[:max_rows]
        if not trimmed:
            return [], [], elapsed

        columns = list(trimmed[0].keys())
        dict_rows = [dict(r) for r in trimmed]
        return columns, dict_rows, elapsed
