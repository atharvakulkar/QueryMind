"""CSV dataset upload service — parse, infer types, create table, bulk insert."""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from core.exceptions import DataUploadError
from database.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Schema where all uploaded datasets are stored.
UPLOAD_SCHEMA = "uploads"

# Pandas dtype → PostgreSQL type mapping.
_DTYPE_MAP: dict[str, str] = {
    "int64": "BIGINT",
    "int32": "INTEGER",
    "Int64": "BIGINT",
    "Int32": "INTEGER",
    "float64": "DOUBLE PRECISION",
    "float32": "REAL",
    "bool": "BOOLEAN",
    "boolean": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
    "datetime64[ns, UTC]": "TIMESTAMPTZ",
    "object": "TEXT",
    "string": "TEXT",
    "category": "TEXT",
}

# Identifier validation — same pattern used by MCP tools.
_IDENT = re.compile(r"^[a-z][a-z0-9_]*$")

# Reserved PostgreSQL words that cannot be used as unquoted identifiers.
_RESERVED = frozenset({
    "select", "from", "where", "table", "index", "order", "group",
    "limit", "offset", "insert", "update", "delete", "create", "drop",
    "alter", "grant", "user", "column", "default", "check", "primary",
    "foreign", "key", "references", "constraint", "null", "not", "and",
    "or", "in", "is", "as", "on", "join", "left", "right", "inner",
    "outer", "cross", "union", "all", "distinct", "having", "between",
    "like", "exists", "case", "when", "then", "else", "end", "with",
    "values", "set", "into", "view", "schema", "database", "trigger",
    "function", "procedure", "true", "false", "type", "cast",
})


@dataclass
class UploadResult:
    """Metadata returned after a successful CSV upload."""

    schema_name: str
    table_name: str
    fully_qualified: str
    row_count: int
    columns: list[dict[str, str]]  # [{"name": ..., "pg_type": ...}, ...]


def sanitize_table_name(filename: str) -> str:
    """Derive a safe PostgreSQL identifier from a CSV filename.

    Examples
    --------
    >>> sanitize_table_name("Sales Data (2024).csv")
    'sales_data_2024'
    """
    name = filename.rsplit(".", 1)[0]  # strip extension
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)  # only alnum and underscores
    name = re.sub(r"_+", "_", name)  # collapse runs
    name = name.strip("_").lower()
    if not name or not name[0].isalpha():
        name = "t_" + name
    # Truncate to 60 chars (PostgreSQL max is 63)
    name = name[:60]
    # Avoid reserved words
    if name in _RESERVED:
        name = f"t_{name}"
    if not _IDENT.match(name):
        raise DataUploadError(
            f"Could not derive a valid table name from '{filename}'.",
            details={"derived": name},
        )
    return name


def _sanitize_column_name(col: str) -> str:
    """Sanitize a single column name."""
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", str(col))
    name = re.sub(r"_+", "_", name).strip("_").lower()
    if not name or not name[0].isalpha():
        name = "c_" + name
    name = name[:60]
    if name in _RESERVED:
        name = f"c_{name}"
    return name


def _pg_type(dtype: Any) -> str:
    """Map a Pandas dtype to a PostgreSQL type string."""
    dtype_str = str(dtype)
    if dtype_str in _DTYPE_MAP:
        return _DTYPE_MAP[dtype_str]
    if "int" in dtype_str.lower():
        return "BIGINT"
    if "float" in dtype_str.lower():
        return "DOUBLE PRECISION"
    if "datetime" in dtype_str.lower():
        return "TIMESTAMP"
    if "bool" in dtype_str.lower():
        return "BOOLEAN"
    return "TEXT"


class CsvUploader:
    """Handles CSV parsing, table creation, and bulk data insertion."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._cm = connection_manager

    async def upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        *,
        table_name_override: str | None = None,
    ) -> UploadResult:
        """Parse CSV, create table in 'uploads' schema, and insert all rows.

        Parameters
        ----------
        file_bytes:
            Raw bytes of the uploaded CSV file.
        original_filename:
            Original filename from the upload (used to derive table name).
        table_name_override:
            Optional explicit table name (must be a valid identifier).

        Returns
        -------
        UploadResult with metadata about the created table.
        """
        # 1. Determine table name
        table_name = table_name_override or sanitize_table_name(original_filename)
        logger.info("Upload: target table → %s.%s", UPLOAD_SCHEMA, table_name)

        # 2. Parse CSV with pandas
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as exc:
            raise DataUploadError(
                "Could not parse the CSV file. Check the format and encoding.",
                details={"reason": str(exc)},
            ) from exc

        if df.empty:
            raise DataUploadError("The CSV file is empty (no rows found).")

        if len(df.columns) == 0:
            raise DataUploadError("The CSV file has no columns.")

        # 3. Sanitize column names and infer types
        original_cols = list(df.columns)
        clean_cols = [_sanitize_column_name(c) for c in original_cols]

        # Handle duplicate column names after sanitisation
        seen: dict[str, int] = {}
        deduped: list[str] = []
        for c in clean_cols:
            if c in seen:
                seen[c] += 1
                deduped.append(f"{c}_{seen[c]}")
            else:
                seen[c] = 0
                deduped.append(c)
        clean_cols = deduped

        df.columns = pd.Index(clean_cols)

        # Try to let pandas infer better dtypes (nullable integers, etc.)
        df = df.convert_dtypes()

        col_defs: list[dict[str, str]] = []
        pg_col_parts: list[str] = []
        for col in clean_cols:
            pg_type = _pg_type(df[col].dtype)
            col_defs.append({"name": col, "pg_type": pg_type})
            pg_col_parts.append(f'    "{col}" {pg_type}')

        # 4. Ensure 'uploads' schema exists
        await self._cm.execute_ddl(f"CREATE SCHEMA IF NOT EXISTS {UPLOAD_SCHEMA}")

        # 5. Drop existing table with same name (replace strategy)
        fq = f"{UPLOAD_SCHEMA}.{table_name}"
        await self._cm.execute_ddl(f"DROP TABLE IF EXISTS {fq}")

        # 6. CREATE TABLE
        cols_sql = ",\n".join(pg_col_parts)
        create_sql = f'CREATE TABLE {fq} (\n{cols_sql}\n)'
        logger.info("Upload DDL:\n%s", create_sql)
        await self._cm.execute_ddl(create_sql)

        # 7. Prepare records for asyncpg COPY
        #    Convert DataFrame rows to list of tuples, handling NaN → None.
        records: list[tuple] = []
        for row in df.itertuples(index=False, name=None):
            cleaned = tuple(
                None if pd.isna(v) else v for v in row
            )
            records.append(cleaned)

        # 8. Bulk insert via COPY protocol
        row_count = await self._cm.copy_records(
            table_name=table_name,
            schema_name=UPLOAD_SCHEMA,
            columns=clean_cols,
            records=records,
        )

        logger.info(
            "Upload complete: %s.%s — %s rows, %s columns.",
            UPLOAD_SCHEMA, table_name, row_count, len(clean_cols),
        )

        return UploadResult(
            schema_name=UPLOAD_SCHEMA,
            table_name=table_name,
            fully_qualified=fq,
            row_count=row_count,
            columns=col_defs,
        )

    async def list_uploaded_tables(self) -> list[dict[str, Any]]:
        """List all tables in the uploads schema."""
        sql = """
        SELECT table_name,
               (SELECT count(*) FROM information_schema.columns c2
                WHERE c2.table_schema = 'uploads' AND c2.table_name = t.table_name) AS column_count
        FROM information_schema.tables t
        WHERE table_schema = 'uploads'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        try:
            _, rows, _ = await self._cm.fetch_all(sql, enforce_guard=False)
            return rows
        except Exception:
            return []

    async def drop_table(self, table_name: str) -> None:
        """Drop an uploaded table by name."""
        if not _IDENT.match(table_name):
            raise DataUploadError(
                f"Invalid table name: {table_name!r}",
                details={"table_name": table_name},
            )
        fq = f"{UPLOAD_SCHEMA}.{table_name}"
        await self._cm.execute_ddl(f"DROP TABLE IF EXISTS {fq}")
        logger.info("Dropped uploaded table: %s", fq)
