"""QueryMind NL→SQL agent: MCP grounding, LangChain (Groq), validation, retries."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.agent.sql_validator import SqlPolicyValidator
from backend.schemas.agent import (
    AgentRunResponse,
    HistoryEntry,
    NLQueryRequest,
    SQLDraft,
    SchemaLink,
)
from core.config import Settings
from core.exceptions import (
    ConfigError,
    MCPConnectionError,
    SQLExecutionError,
    SQLGenerationError,
    SchemaLinkingError,
)
from database.connection_manager import ConnectionManager
from database.schema_catalog import SchemaCatalog
from mcp_server.client import McpSchemaClient

logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict[str, Any]:
    """Strip optional markdown fences and parse JSON object."""
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    return json.loads(raw)


class QueryMindAgent:
    """Orchestrates schema linking, SQL generation, AST validation, and execution."""

    def __init__(
        self,
        settings: Settings,
        connection_manager: ConnectionManager,
        mcp_client: McpSchemaClient,
        llm: ChatGroq | None = None,
    ) -> None:
        self._settings = settings
        self._cm = connection_manager
        self._mcp = mcp_client
        self._llm = llm

    def _get_llm(self) -> ChatGroq:
        if self._llm is not None:
            return self._llm
        if not self._settings.groq_api_key:
            raise ConfigError(
                "GROQ_API_KEY is required for the NL→SQL agent.",
                details={"hint": "Set GROQ_API_KEY in the environment."},
            )
        return ChatGroq(
            api_key=self._settings.groq_api_key,
            model=self._settings.groq_model,
            temperature=0,
        )

    async def run(self, request: NLQueryRequest) -> AgentRunResponse:
        request_id = str(uuid.uuid4())[:8]
        cap = min(
            request.max_rows or self._settings.max_query_rows,
            self._settings.max_query_rows,
        )
        validator = SqlPolicyValidator(cap)
        llm = self._get_llm()

        logger.info("[%s] Agent run started.", request_id)

        try:
            summary = await self._mcp.export_schema_summary()
        except MCPConnectionError:
            raise
        except Exception as exc:
            logger.exception("[%s] MCP export_schema_summary failed.", request_id)
            raise MCPConnectionError(
                "Failed to load schema from MCP.",
                details={"reason": str(exc)},
            ) from exc

        catalog = SchemaCatalog.from_mcp_summary(summary)
        if not catalog.allowed_tables:
            raise SchemaLinkingError(
                "No tables found via MCP for this database.",
                details={"hint": "Check DATABASE_URL and permissions."},
            )

        schema_link = await self._schema_linking(
            llm, request.question, summary, request_id, request.history,
        )

        if not schema_link.tables:
            raise SchemaLinkingError(
                "Schema link must include at least one table from the catalog.",
                details={},
            )

        try:
            catalog.validate_schema_link_tables(schema_link.tables)
            if schema_link.columns:
                catalog.validate_schema_link_columns(schema_link.columns)
        except ValueError as exc:
            raise SchemaLinkingError(
                str(exc),
                details={"schema_link": schema_link.model_dump()},
            ) from exc

        table_details: list[str] = []
        for fq in schema_link.tables:
            parts = fq.split(".", 1)
            if len(parts) != 2:
                raise SchemaLinkingError(
                    f"Table {fq!r} must be schema.table form.",
                    details={},
                )
            schema_name, table_name = parts
            try:
                desc = await self._mcp.describe_table(schema_name, table_name)
            except MCPConnectionError:
                raise
            except Exception as exc:
                logger.exception("[%s] describe_table failed.", request_id)
                raise MCPConnectionError(
                    "Failed to describe table via MCP.",
                    details={"table": fq, "reason": str(exc)},
                ) from exc
            table_details.append(json.dumps(desc, indent=2))

        context_block = "\n\n".join(table_details)
        max_attempts = self._settings.agent_max_retries
        feedback: str | None = None
        last_sql: str | None = None

        for attempt in range(1, max_attempts + 1):
            sql: str | None = None
            try:
                draft = await self._sql_generation(
                    llm,
                    request.question,
                    schema_link,
                    context_block,
                    request_id,
                    attempt,
                    feedback,
                    last_sql,
                    request.history,
                )
                sql = draft.sql.strip()
                if self._settings.log_agent_sql:
                    logger.info("[%s] Generated SQL (attempt %s): %s", request_id, attempt, sql)

                validated = validator.validate(sql, catalog)
                cols, rows, elapsed = await self._cm.fetch_all(
                    validated,
                    enforce_guard=False,
                )

                warnings: list[str] = []
                if attempt > 1:
                    warnings.append(f"Succeeded after {attempt} attempt(s).")

                # Generate an executive insight summary after successful execution
                insights = await self._generate_insights(
                    llm, request.question, validated, cols, rows, request_id,
                )

                return AgentRunResponse(
                    final_sql=validated,
                    columns=cols,
                    rows=rows,
                    execution_time_ms=round(elapsed * 1000, 3),
                    retries_used=attempt - 1,
                    schema_link=schema_link,
                    warnings=warnings,
                    assumptions=draft.assumptions,
                    insights=insights,
                )
            except (SQLExecutionError, ValueError) as exc:
                feedback = getattr(exc, "message", str(exc))
                details = getattr(exc, "details", None) or {}
                logger.warning(
                    "[%s] Attempt %s failed: %s %s",
                    request_id,
                    attempt,
                    feedback,
                    details,
                )
                if attempt == max_attempts:
                    raise SQLGenerationError(
                        "Could not produce executable SQL within retry budget.",
                        details={
                            "last_error": feedback,
                            "attempts": max_attempts,
                        },
                    ) from exc
                last_sql = sql
                continue

        raise SQLGenerationError(
            "Unexpected agent failure.",
            details={"request_id": request_id},
        )

    async def _schema_linking(
        self,
        llm: ChatGroq,
        question: str,
        summary: dict[str, Any],
        request_id: str,
        history: list[HistoryEntry] | None = None,
    ) -> SchemaLink:
        system = SystemMessage(
            content=(
                "You are a careful analytics engineer. Output ONLY a single JSON object with keys: "
                "tables (array of strings 'schema.table'), columns (array of strings "
                "'schema.table.column'), join_hints (array of short strings). "
                "Only include tables and columns that exist in the schema summary. "
                "No markdown, no explanation."
            ),
        )
        human = HumanMessage(
            content=(
                f"Schema summary JSON:\n{json.dumps(summary, indent=2)[:12000]}\n\n"
                f"Question:\n{question}"
            ),
        )
        # Build message list with conversational history
        messages: list = [system]
        if history:
            for entry in history[-4:]:
                if entry.role == "user":
                    messages.append(HumanMessage(content=entry.content))
                else:
                    messages.append(AIMessage(content=entry.content))
        messages.append(human)
        out = await asyncio.to_thread(llm.invoke, messages)
        text = out.content if isinstance(out.content, str) else str(out.content)
        try:
            data = _extract_json_object(text)
            return SchemaLink.model_validate(data)
        except Exception as exc:
            logger.exception("[%s] Schema linking parse failed.", request_id)
            raise SchemaLinkingError(
                "Model did not return valid schema link JSON.",
                details={"raw": text[:2000], "reason": str(exc)},
            ) from exc

    async def _sql_generation(
        self,
        llm: ChatGroq,
        question: str,
        link: SchemaLink,
        table_context: str,
        request_id: str,
        attempt: int,
        feedback: str | None,
        last_sql: str | None,
        history: list[HistoryEntry] | None = None,
    ) -> SQLDraft:
        system = SystemMessage(
            content=(
                "You are a PostgreSQL expert. Output ONLY a JSON object with keys: "
                "sql (string, a single SELECT or WITH ... SELECT only), "
                "assumptions (array of short strings), "
                "insights (string, a one or two sentence executive summary predicting what "
                "the data will show based on the question — e.g. 'This should reveal the "
                "top regions by revenue for Q3.'). "
                "Use schema-qualified table names. Qualify columns with table aliases when needed. "
                "No semicolons after the query. No markdown."
            ),
        )
        parts = [
            f"Question:\n{question}",
            f"Schema link:\n{json.dumps(link.model_dump(), indent=2)}",
            f"Table metadata:\n{table_context[:14000]}",
            f"Attempt: {attempt}",
        ]
        if feedback:
            parts.append(f"Previous error (fix the SQL):\n{feedback}")
        if last_sql:
            parts.append(f"Previous SQL:\n{last_sql}")
        human = HumanMessage(content="\n\n".join(parts))

        # Build messages with conversational context
        messages: list = [system]
        if history:
            for entry in history[-4:]:
                if entry.role == "user":
                    messages.append(HumanMessage(content=entry.content))
                else:
                    messages.append(AIMessage(content=entry.content))
        messages.append(human)

        out = await asyncio.to_thread(llm.invoke, messages)
        text = out.content if isinstance(out.content, str) else str(out.content)
        try:
            data = _extract_json_object(text)
            return SQLDraft.model_validate(data)
        except Exception as exc:
            logger.exception("[%s] SQL draft parse failed.", request_id)
            raise SQLExecutionError(
                "Model did not return valid SQL draft JSON.",
                code="sql_generation_parse_error",
                details={"raw": text[:2000], "reason": str(exc)},
            ) from exc

    async def _generate_insights(
        self,
        llm: ChatGroq,
        question: str,
        sql: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        request_id: str,
    ) -> str | None:
        """Best-effort executive summary of query results."""
        if not rows:
            return None
        try:
            # Limit to first 20 rows to keep prompt short
            sample = rows[:20]
            system = SystemMessage(
                content=(
                    "You are a data analyst. Given a business question, the SQL that answered it, "
                    "and a sample of the results, write a concise 1-2 sentence executive summary "
                    "of the key insight. Be specific with numbers when available. "
                    "Output ONLY the insight text, no JSON, no markdown."
                ),
            )
            human = HumanMessage(
                content=(
                    f"Question: {question}\n\n"
                    f"SQL: {sql}\n\n"
                    f"Columns: {columns}\n\n"
                    f"Sample rows ({len(sample)} of {len(rows)} total):\n"
                    f"{json.dumps(sample, indent=2, default=str)[:6000]}"
                ),
            )
            out = await asyncio.to_thread(llm.invoke, [system, human])
            text = out.content if isinstance(out.content, str) else str(out.content)
            insight = text.strip()
            if insight:
                logger.info("[%s] Insights generated.", request_id)
                return insight
            return None
        except Exception:
            logger.warning("[%s] Insights generation failed (non-fatal).", request_id, exc_info=True)
            return None
