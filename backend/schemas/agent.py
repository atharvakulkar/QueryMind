"""Pydantic models for the NL→SQL agent (Phases 3–5)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A single turn in the conversation history sent by the frontend."""

    role: Literal["user", "assistant"] = Field(
        description="Who produced this message.",
    )
    content: str = Field(
        min_length=1,
        max_length=20_000,
        description="The text of the message (question or summary).",
    )


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
    history: list[HistoryEntry] = Field(
        default_factory=list,
        max_length=20,
        description="Rolling window of previous conversation turns for multi-turn context.",
    )


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
    """LLM-generated SQL plus explicit assumptions and optional insight."""

    sql: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    insights: str | None = Field(
        default=None,
        description="One or two sentence executive summary of what the data likely shows.",
    )


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
    insights: str | None = Field(
        default=None,
        description="LLM-generated executive summary of the query results.",
    )
