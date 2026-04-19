"""Pytest fixtures."""

from typing import Any

import pytest

from core.config import Settings


@pytest.fixture()
def test_settings() -> Settings:
    """Minimal settings for unit tests (no live database)."""
    return Settings.model_validate(
        {
            "database_url": "postgresql://user:pass@127.0.0.1:65432/querymind_test",
            "allow_adhoc_sql": False,
            "max_query_rows": 100,
            "statement_timeout_seconds": 10,
        },
    )


class FakeConnectionManager:
    """In-memory stand-in for asyncpg-backed ConnectionManager."""

    def __init__(
        self,
        *,
        healthy: bool = True,
        fetch_result: tuple[list[str], list[dict[str, Any]], float] | None = None,
    ) -> None:
        self.healthy = healthy
        self.fetch_result = fetch_result or (
            ["database", "server_time"],
            [{"database": "querymind_test", "server_time": "2099-01-01T00:00:00"}],
            0.002,
        )
        self.closed = False

    async def health_check(self) -> bool:
        return self.healthy

    async def fetch_all(
        self,
        sql: str,
        *,
        params: tuple[Any, ...] | list[Any] | None = None,
        enforce_guard: bool = True,
    ) -> tuple[list[str], list[dict[str, Any]], float]:
        return self.fetch_result

    async def close(self) -> None:
        self.closed = True


@pytest.fixture()
def fake_cm() -> FakeConnectionManager:
    return FakeConnectionManager()
