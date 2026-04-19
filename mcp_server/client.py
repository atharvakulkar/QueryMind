"""MCP stdio client for schema tools (used by the FastAPI agent)."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.config import Settings
from core.exceptions import MCPConnectionError

logger = logging.getLogger(__name__)

QUERYMIND_ROOT = Path(__file__).resolve().parent.parent


def _tool_result_to_text(result: Any) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


class McpSchemaClient:
    """
    Spawns `python -m mcp_server.server` over stdio and exposes schema tools.

    One subprocess is started per `_with_session` call (per agent request by default).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _stdio_params(self) -> StdioServerParameters:
        cwd = self._settings.mcp_server_cwd or str(QUERYMIND_ROOT)
        env = dict(os.environ)
        env["DATABASE_URL"] = str(self._settings.database_url)
        # Ensure Python can import project packages when cwd is project root
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{cwd}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = cwd
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "mcp_server.server"],
            cwd=cwd,
            env=env,
        )

    async def _with_session(self, fn: Any) -> Any:
        params = self._stdio_params()
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await fn(session)
        except Exception as exc:
            logger.exception("MCP stdio session failed.")
            raise MCPConnectionError(
                "Could not connect to the MCP schema server.",
                details={"reason": str(exc)},
            ) from exc

    async def export_schema_summary(self) -> dict[str, Any]:
        """Call tool `export_schema_summary` and parse JSON."""

        async def _call(session: ClientSession) -> dict[str, Any]:
            result = await session.call_tool("export_schema_summary", {})
            text = _tool_result_to_text(result)
            return json.loads(text)

        return await self._with_session(_call)

    async def list_tables(self, schema_name: str | None = None) -> dict[str, Any]:
        """Call tool `list_tables`."""

        async def _call(session: ClientSession) -> dict[str, Any]:
            args: dict[str, Any] = {}
            if schema_name is not None and str(schema_name).strip():
                args["schema_name"] = schema_name
            result = await session.call_tool("list_tables", args)
            text = _tool_result_to_text(result)
            return json.loads(text)

        return await self._with_session(_call)

    async def describe_table(self, schema_name: str, table_name: str) -> dict[str, Any]:
        """Call tool `describe_table`."""

        async def _call(session: ClientSession) -> dict[str, Any]:
            result = await session.call_tool(
                "describe_table",
                {"schema_name": schema_name, "table_name": table_name},
            )
            text = _tool_result_to_text(result)
            return json.loads(text)

        return await self._with_session(_call)
