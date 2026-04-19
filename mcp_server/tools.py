"""MCP tool implementations (metadata only; no arbitrary SQL from clients)."""

from __future__ import annotations

import json
import logging
import re

from database.schema_introspector import SchemaIntrospector

logger = logging.getLogger(__name__)

_IDENT = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_identifier(value: str | None, field: str) -> str:
    """Restrict dynamic parts of tool arguments to simple SQL identifiers."""
    if value is None or not str(value).strip():
        raise ValueError(f"{field} is required.")
    text = str(value).strip()
    if not _IDENT.match(text):
        raise ValueError(f"Invalid identifier for {field}: {value!r}.")
    return text


async def tool_list_tables(
    introspector: SchemaIntrospector,
    schema_name: str | None = None,
) -> str:
    """Return JSON list of tables (and views) in user schemas."""
    if schema_name is not None and str(schema_name).strip():
        validate_identifier(schema_name, "schema_name")
    schema = await introspector.introspect_full()
    tables = [
        {"schema": t.schema_name, "name": t.name, "type": t.table_type}
        for t in schema.tables
        if not schema_name or t.schema_name == schema_name
    ]
    payload = {"tables": tables}
    logger.info("MCP list_tables returned %s tables.", len(tables))
    return json.dumps(payload, indent=2)


async def tool_describe_table(
    introspector: SchemaIntrospector,
    schema_name: str,
    table_name: str,
) -> str:
    """Return full JSON metadata for a single table."""
    schema_name = validate_identifier(schema_name, "schema_name")
    table_name = validate_identifier(table_name, "table_name")
    schema = await introspector.introspect_full()
    for table in schema.tables:
        if table.schema_name == schema_name and table.name == table_name:
            logger.info("MCP describe_table hit %s.%s", schema_name, table_name)
            return table.model_dump_json(indent=2)
    logger.info("MCP describe_table miss %s.%s", schema_name, table_name)
    return json.dumps(
        {"error": "not_found", "schema": schema_name, "table": table_name},
        indent=2,
    )


async def tool_export_schema_summary(introspector: SchemaIntrospector) -> str:
    """Return a compact JSON summary suitable for LLM context windows."""
    schema = await introspector.introspect_full()
    compact = {
        "tables": [
            {
                "schema": t.schema_name,
                "name": t.name,
                "columns": [c.name for c in t.columns],
                "foreign_keys": [
                    f"{fk.column_name}->{fk.referenced_table}.{fk.referenced_column}"
                    for fk in t.foreign_keys
                ],
            }
            for t in schema.tables
        ]
    }
    logger.info("MCP export_schema_summary for %s tables.", len(compact["tables"]))
    return json.dumps(compact, indent=2)
