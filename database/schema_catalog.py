"""Schema catalog built from MCP export for identifier allowlisting."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


def _norm_ident(s: str) -> str:
    return s.strip().lower()


@dataclass
class SchemaCatalog:
    """Allowlisted tables and columns from MCP `export_schema_summary` JSON."""

    allowed_tables: set[str] = field(default_factory=set)
    allowed_columns: set[str] = field(default_factory=set)
    columns_by_table: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def from_mcp_summary(cls, data: dict) -> SchemaCatalog:
        """Build catalog from MCP tool_export_schema_summary payload."""
        cat = cls()
        tables = data.get("tables") or []
        for t in tables:
            schema = str(t.get("schema", "public"))
            name = str(t.get("name", ""))
            if not name:
                continue
            fq = _norm_ident(f"{schema}.{name}")
            cat.allowed_tables.add(fq)
            cols = t.get("columns") or []
            col_set: set[str] = set()
            for c in cols:
                cn = _norm_ident(str(c))
                col_set.add(cn)
                cat.allowed_columns.add(f"{fq}.{cn}")
            cat.columns_by_table[fq] = col_set
        logger.debug("SchemaCatalog: %s tables, %s columns.", len(cat.allowed_tables), len(cat.allowed_columns))
        return cat

    def validate_schema_link_tables(self, tables: list[str]) -> None:
        """Raise ValueError if any table is not in the catalog."""
        for raw in tables:
            key = _norm_ident(raw)
            if key not in self.allowed_tables:
                raise ValueError(f"Unknown table in schema link: {raw!r}")

    def validate_schema_link_columns(self, columns: list[str]) -> None:
        """Raise ValueError if any column FQN is not in the catalog."""
        for raw in columns:
            key = _norm_ident(raw)
            if key not in self.allowed_columns:
                raise ValueError(f"Unknown column in schema link: {raw!r}")
