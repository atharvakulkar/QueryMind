"""MCP stdio server entrypoint for QueryMind schema tools."""

from __future__ import annotations

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from core.config import get_settings
from core.logging_config import configure_logging
from database.connection_manager import ConnectionManager
from database.schema_introspector import SchemaIntrospector
from mcp_server import tools as mcp_tools

logger = logging.getLogger(__name__)


def _build_server(introspector: SchemaIntrospector) -> Server:
    server = Server("querymind-schema")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_tables",
                description=(
                    "List tables and views in non-system schemas. "
                    "Optional schema_name filters to a single schema."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Optional schema name filter.",
                        },
                    },
                },
            ),
            Tool(
                name="describe_table",
                description="Return columns and foreign keys for one table.",
                inputSchema={
                    "type": "object",
                    "required": ["schema_name", "table_name"],
                    "properties": {
                        "schema_name": {"type": "string"},
                        "table_name": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="export_schema_summary",
                description="Export a compact JSON summary of the database schema.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        arguments = arguments or {}
        try:
            if name == "list_tables":
                text = await mcp_tools.tool_list_tables(
                    introspector,
                    arguments.get("schema_name"),
                )
            elif name == "describe_table":
                text = await mcp_tools.tool_describe_table(
                    introspector,
                    str(arguments.get("schema_name", "")),
                    str(arguments.get("table_name", "")),
                )
            elif name == "export_schema_summary":
                text = await mcp_tools.tool_export_schema_summary(introspector)
            else:
                text = json.dumps({"error": "unknown_tool", "name": name})
            return [TextContent(type="text", text=text)]
        except ValueError as exc:
            logger.warning("MCP tool validation error: %s", exc)
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]

    return server


async def _amain() -> None:
    settings = get_settings()
    # core.logging_config attaches handlers to stderr (safe for stdio MCP).
    configure_logging(settings.log_level)
    cm = ConnectionManager(settings)
    await cm.connect()
    introspector = SchemaIntrospector(cm)
    server = _build_server(introspector)
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("QueryMind MCP schema server listening on stdio.")
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await cm.close()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
