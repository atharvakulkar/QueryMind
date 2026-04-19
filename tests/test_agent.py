"""Tests for QueryMindAgent with mocked Groq, MCP, and database."""

from __future__ import annotations

import json
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from backend.agent.agent_engine import QueryMindAgent
from backend.schemas.agent import NLQueryRequest
from core.config import Settings
from core.exceptions import SchemaLinkingError, SQLGenerationError


class FakeLLM:
    """Deterministic LangChain-compatible chat model."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    def invoke(self, messages: list[Any]) -> AIMessage:
        if not self._responses:
            raise RuntimeError("FakeLLM: no more canned responses.")
        return AIMessage(content=self._responses.pop(0))


class FakeMcpClient:
    """Stub MCP client returning fixed schema payloads."""

    def __init__(self) -> None:
        self.describe_calls: list[tuple[str, str]] = []

    async def export_schema_summary(self) -> dict[str, Any]:
        return {
            "tables": [
                {
                    "schema": "public",
                    "name": "users",
                    "columns": ["id", "name"],
                    "foreign_keys": [],
                },
                {
                    "schema": "public",
                    "name": "orders",
                    "columns": ["id", "user_id", "total"],
                    "foreign_keys": ["user_id->users.id"],
                },
            ],
        }

    async def list_tables(self, schema_name: str | None = None) -> dict[str, Any]:
        return {"tables": []}

    async def describe_table(self, schema_name: str, table_name: str) -> dict[str, Any]:
        self.describe_calls.append((schema_name, table_name))
        return {
            "schema_name": schema_name,
            "name": table_name,
            "columns": [{"name": "id"}, {"name": "name"}],
        }


class SpyConnectionManager:
    """Records fetch calls and can fail the first N times."""

    def __init__(self, fail_first_n: int = 0) -> None:
        self.fail_first_n = fail_first_n
        self._calls = 0
        self.queries: list[str] = []

    async def fetch_all(
        self,
        sql: str,
        *,
        params: tuple[Any, ...] | list[Any] | None = None,
        enforce_guard: bool = True,
    ) -> tuple[list[str], list[dict[str, Any]], float]:
        self._calls += 1
        self.queries.append(sql)
        if self._calls <= self.fail_first_n:
            from core.exceptions import SQLExecutionError

            raise SQLExecutionError(
                "Simulated DB error.",
                details={"reason": "unit_test"},
            )
        return (
            ["id", "name"],
            [{"id": 1, "name": "Ada"}],
            0.001,
        )


def _settings() -> Settings:
    return Settings.model_validate(
        {
            "database_url": "postgresql://u:p@127.0.0.1:1/t",
            "groq_api_key": "test-key",
            "agent_max_retries": 3,
        },
    )


@pytest.mark.asyncio
async def test_agent_join_happy_path() -> None:
    schema_link = json.dumps(
        {
            "tables": ["public.users", "public.orders"],
            "columns": ["public.users.id", "public.orders.user_id"],
            "join_hints": ["users.id = orders.user_id"],
        },
    )
    sql_ok = json.dumps(
        {
            "sql": (
                "SELECT u.id, o.total FROM public.users AS u "
                "JOIN public.orders AS o ON u.id = o.user_id"
            ),
            "assumptions": ["Join users to orders on user id."],
        },
    )
    llm = FakeLLM([schema_link, sql_ok])
    agent = QueryMindAgent(
        _settings(),
        SpyConnectionManager(),
        FakeMcpClient(),
        llm=llm,
    )
    out = await agent.run(NLQueryRequest(question="Show user ids with order totals."))
    assert "JOIN" in out.final_sql.upper()
    assert out.rows
    assert out.retries_used == 0


@pytest.mark.asyncio
async def test_schema_link_unknown_table() -> None:
    schema_link = json.dumps(
        {
            "tables": ["public.does_not_exist"],
            "columns": [],
            "join_hints": [],
        },
    )
    llm = FakeLLM([schema_link])
    agent = QueryMindAgent(
        _settings(),
        SpyConnectionManager(),
        FakeMcpClient(),
        llm=llm,
    )
    with pytest.raises(SchemaLinkingError):
        await agent.run(NLQueryRequest(question="bad"))


@pytest.mark.asyncio
async def test_injection_drop_blocked_no_successful_execute() -> None:
    schema_link = json.dumps(
        {
            "tables": ["public.users"],
            "columns": ["public.users.id"],
            "join_hints": [],
        },
    )
    bad_sql = json.dumps({"sql": "DROP TABLE public.users", "assumptions": []})
    good_sql = json.dumps(
        {
            "sql": "SELECT public.users.id FROM public.users",
            "assumptions": [],
        },
    )
    llm = FakeLLM([schema_link, bad_sql, good_sql])
    spy = SpyConnectionManager()
    agent = QueryMindAgent(_settings(), spy, FakeMcpClient(), llm=llm)
    out = await agent.run(NLQueryRequest(question="evil"))
    assert "DROP" not in " ".join(spy.queries).upper()
    assert "SELECT" in out.final_sql.upper()
    assert out.retries_used >= 1


@pytest.mark.asyncio
async def test_retry_on_db_error_then_success() -> None:
    schema_link = json.dumps(
        {
            "tables": ["public.users"],
            "columns": ["public.users.id"],
            "join_hints": [],
        },
    )
    sql = json.dumps(
        {
            "sql": "SELECT public.users.id FROM public.users",
            "assumptions": [],
        },
    )
    llm = FakeLLM([schema_link, sql, sql])
    spy = SpyConnectionManager(fail_first_n=1)
    agent = QueryMindAgent(_settings(), spy, FakeMcpClient(), llm=llm)
    out = await agent.run(NLQueryRequest(question="retry test"))
    assert out.retries_used == 1
    assert len(spy.queries) == 2


@pytest.mark.asyncio
async def test_exhaust_retries_raises() -> None:
    schema_link = json.dumps(
        {
            "tables": ["public.users"],
            "columns": ["public.users.id"],
            "join_hints": [],
        },
    )
    bad = json.dumps({"sql": "DROP TABLE public.users", "assumptions": []})
    llm = FakeLLM([schema_link, bad, bad, bad])
    agent = QueryMindAgent(_settings(), SpyConnectionManager(), FakeMcpClient(), llm=llm)
    with pytest.raises(SQLGenerationError):
        await agent.run(NLQueryRequest(question="x"))
