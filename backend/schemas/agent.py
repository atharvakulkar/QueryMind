"""Pydantic models for the NL→SQL agent (Phase 3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NLQueryRequest(BaseModel):
    """Natural language question for the agent."""

    question: str = Field(min_length=1, max_length=10_000)
    max_rows: int | None = Field(
        default=None,
        ge=1,
        le=10_000,
        description="Override default row cap for this request (clamped to server max).",
    )
    dialect: str = Field(default="postgres", description="SQL dialect hint for the LLM.")


class SchemaLink(BaseModel):
    """Structured schema linking output (tables/columns the query may use)."""

    tables: list[str] = Field(
        default_factory=list,
        description="Fully qualified table names: schema.table",
    )
    columns: list[str] = Field(
        default_factory=list,
        description="Fully qualified column names: schema.table.column",
    )
    join_hints: list[str] = Field(
        default_factory=list,
        description="Optional human-readable join or filter intent.",
    )


class SQLDraft(BaseModel):
    """LLM-generated SQL plus explicit assumptions."""

    sql: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class AgentRunResponse(BaseModel):
    """Successful agent run with results and trace metadata."""

    final_sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float
    retries_used: int
    schema_link: SchemaLink
    warnings: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
