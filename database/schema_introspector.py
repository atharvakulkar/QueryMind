"""Read-only PostgreSQL schema introspection via information_schema."""

from __future__ import annotations

import logging

from database.connection_manager import ConnectionManager
from database.schema_models import (
    ColumnInfo,
    DatabaseSchema,
    ForeignKeyInfo,
    TableInfo,
)

logger = logging.getLogger(__name__)

_LIST_TABLES_SQL = """
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  AND table_type IN ('BASE TABLE', 'VIEW')
ORDER BY table_schema, table_name;
"""

_COLUMNS_SQL = """
SELECT table_schema, table_name, column_name, data_type, is_nullable, ordinal_position
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name, ordinal_position;
"""

_FK_SQL = """
SELECT
    tc.table_schema,
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY tc.table_schema, tc.table_name, tc.constraint_name, kcu.ordinal_position;
"""


class SchemaIntrospector:
    """Builds structured DatabaseSchema snapshots using ConnectionManager."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager

    async def introspect_full(self) -> DatabaseSchema:
        """Load tables, columns, and foreign keys."""
        _, col_rows, _ = await self._cm.fetch_all(_COLUMNS_SQL, enforce_guard=False)
        _, tab_rows, _ = await self._cm.fetch_all(_LIST_TABLES_SQL, enforce_guard=False)
        _, fk_row_dicts, _ = await self._cm.fetch_all(_FK_SQL, enforce_guard=False)

        columns_by_table: dict[tuple[str, str], list[ColumnInfo]] = {}
        for r in col_rows:
            key = (r["table_schema"], r["table_name"])
            columns_by_table.setdefault(key, []).append(
                ColumnInfo(
                    name=r["column_name"],
                    data_type=r["data_type"],
                    is_nullable=(str(r["is_nullable"]).upper() == "YES"),
                    ordinal_position=int(r["ordinal_position"]),
                )
            )

        fk_map: dict[tuple[str, str], list[ForeignKeyInfo]] = {}
        for r in fk_row_dicts:
            key = (r["table_schema"], r["table_name"])
            fk_map.setdefault(key, []).append(
                ForeignKeyInfo(
                    constraint_name=r["constraint_name"],
                    column_name=r["column_name"],
                    referenced_schema=r["foreign_table_schema"],
                    referenced_table=r["foreign_table_name"],
                    referenced_column=r["foreign_column_name"],
                )
            )

        tables: list[TableInfo] = []
        for r in tab_rows:
            key = (r["table_schema"], r["table_name"])
            tables.append(
                TableInfo(
                    schema_name=r["table_schema"],
                    name=r["table_name"],
                    table_type=r.get("table_type", "BASE TABLE"),
                    columns=sorted(
                        columns_by_table.get(key, []),
                        key=lambda c: c.ordinal_position,
                    ),
                    foreign_keys=fk_map.get(key, []),
                )
            )

        logger.info("Schema introspection complete: %s tables.", len(tables))
        return DatabaseSchema(tables=tables)
