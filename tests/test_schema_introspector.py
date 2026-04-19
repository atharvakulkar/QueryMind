"""Tests for schema introspection (mocked database)."""

import pytest

from core.config import Settings
from database.connection_manager import ConnectionManager
from database.schema_introspector import SchemaIntrospector


class StubConnectionManager(ConnectionManager):
    """Returns canned information_schema rows without touching PostgreSQL."""

    def __init__(self) -> None:
        settings = Settings.model_validate(
            {"database_url": "postgresql://user:pass@127.0.0.1:1/stub"},
        )
        super().__init__(settings)

    async def fetch_all(
        self,
        sql: str,
        *,
        params: tuple | list | None = None,
        enforce_guard: bool = True,
    ):
        if "information_schema.tables" in sql and "table_type" in sql:
            return (
                ["table_schema", "table_name", "table_type"],
                [
                    {
                        "table_schema": "public",
                        "table_name": "orders",
                        "table_type": "BASE TABLE",
                    },
                ],
                0.01,
            )
        if "information_schema.columns" in sql:
            return (
                [
                    "table_schema",
                    "table_name",
                    "column_name",
                    "data_type",
                    "is_nullable",
                    "ordinal_position",
                ],
                [
                    {
                        "table_schema": "public",
                        "table_name": "orders",
                        "column_name": "id",
                        "data_type": "integer",
                        "is_nullable": "NO",
                        "ordinal_position": 1,
                    },
                    {
                        "table_schema": "public",
                        "table_name": "orders",
                        "column_name": "total",
                        "data_type": "numeric",
                        "is_nullable": "YES",
                        "ordinal_position": 2,
                    },
                ],
                0.02,
            )
        if "FOREIGN KEY" in sql:
            return (
                [
                    "table_schema",
                    "table_name",
                    "constraint_name",
                    "column_name",
                    "foreign_table_schema",
                    "foreign_table_name",
                    "foreign_column_name",
                ],
                [],
                0.01,
            )
        raise AssertionError(f"Unexpected SQL in stub: {sql[:120]!r}")


@pytest.mark.asyncio
async def test_introspector_orders_table() -> None:
    intro = SchemaIntrospector(StubConnectionManager())
    schema = await intro.introspect_full()
    assert len(schema.tables) == 1
    table = schema.tables[0]
    assert table.schema_name == "public"
    assert table.name == "orders"
    assert [c.name for c in table.columns] == ["id", "total"]
