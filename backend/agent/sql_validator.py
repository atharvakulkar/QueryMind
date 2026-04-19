"""AST-based SQL policy validation using sqlglot."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import sqlglot
from sqlglot import exp

from core.exceptions import SQLExecutionError

if TYPE_CHECKING:
    from database.schema_catalog import SchemaCatalog

logger = logging.getLogger(__name__)

_DANGEROUS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
)


class SqlPolicyValidator:
    """Validate generated SQL against read-only policy and schema catalog."""

    def __init__(self, max_rows: int) -> None:
        self._max_rows = max_rows

    def validate(self, sql: str, catalog: SchemaCatalog) -> str:
        """
        Validate SQL and return executable SQL (appends LIMIT if missing).

        Raises
        ------
        SQLExecutionError
            On policy or schema violations.
        """
        stripped = sql.strip()
        if not stripped:
            raise SQLExecutionError("Empty SQL.", code="sql_not_allowed")

        if re.search(r";\s*\S", stripped):
            raise SQLExecutionError(
                "Multiple statements are not allowed.",
                code="sql_not_allowed",
            )

        try:
            statements = sqlglot.parse(stripped, dialect="postgres")
        except Exception as exc:
            logger.info("sqlglot parse failed: %s", exc)
            raise SQLExecutionError(
                "SQL could not be parsed for validation.",
                code="sql_validation_error",
                details={"reason": str(exc)},
            ) from exc

        if len(statements) != 1:
            raise SQLExecutionError(
                "Exactly one SQL statement is required.",
                code="sql_not_allowed",
            )

        root = statements[0]
        if not isinstance(root, (exp.Select, exp.With, exp.Union)):
            raise SQLExecutionError(
                "Only SELECT queries (including WITH / UNION) are allowed.",
                code="sql_not_allowed",
            )

        for bad in _DANGEROUS:
            if root.find(bad):
                raise SQLExecutionError(
                    f"Disallowed statement type: {bad.__name__}.",
                    code="sql_not_allowed",
                )

        for node in root.walk():
            for bad in _DANGEROUS:
                if isinstance(node, bad):
                    raise SQLExecutionError(
                        f"Disallowed construct: {bad.__name__}.",
                        code="sql_not_allowed",
                    )

        self._check_catalog(root, catalog)

        sql_out = root.sql(dialect="postgres").strip()
        if root.find(exp.Limit) is None:
            sql_out = f"{sql_out} LIMIT {self._max_rows}"
        return sql_out

    def _check_catalog(self, root: exp.Expression, catalog: SchemaCatalog) -> None:
        """Ensure tables/columns exist in SchemaCatalog."""
        alias_to_fq: dict[str, str] = {}

        for table in root.find_all(exp.Table):
            if isinstance(table.this, exp.Subquery):
                continue
            fq = self._resolve_table_fq(table, catalog)
            al = table.alias
            if al:
                alias_to_fq[str(al).lower()] = fq
            alias_to_fq[fq.split(".")[-1]] = fq

        for column in root.find_all(exp.Column):
            ctable = column.args.get("table")
            cname = column.name
            if not cname:
                continue
            cname_l = str(cname).lower()
            if ctable:
                key = str(ctable).lower()
                fq_table = alias_to_fq.get(key)
                if fq_table is None and "." in key:
                    fq_table = key
                if fq_table is None:
                    raise SQLExecutionError(
                        f"Could not resolve column qualifier {key!r}.",
                        code="sql_validation_error",
                    )
                full = f"{fq_table}.{cname_l}"
                if full not in catalog.allowed_columns:
                    raise SQLExecutionError(
                        f"Column not in catalog: {full}",
                        code="sql_validation_error",
                    )
            else:
                matches = [
                    t
                    for t in catalog.allowed_columns
                    if t.endswith("." + cname_l)
                ]
                if len(matches) != 1:
                    raise SQLExecutionError(
                        f"Ambiguous or unknown unqualified column {cname_l!r}.",
                        code="sql_validation_error",
                        details={"matches": matches[:10]},
                    )

    def _resolve_table_fq(self, table: exp.Table, catalog: SchemaCatalog) -> str:
        name = table.name
        if not name:
            raise SQLExecutionError("Unsupported table expression.", code="sql_validation_error")
        db = table.db
        if db:
            fq = f"{db}.{name}".lower()
        else:
            short = str(name).lower()
            candidates = [t for t in catalog.allowed_tables if t.endswith("." + short)]
            if len(candidates) != 1:
                raise SQLExecutionError(
                    f"Table {name!r} must be schema-qualified or uniquely named.",
                    code="sql_validation_error",
                    details={"candidates": candidates[:20]},
                )
            fq = candidates[0]
        if fq not in catalog.allowed_tables:
            raise SQLExecutionError(
                f"Table not allowed: {fq}",
                code="sql_validation_error",
            )
        return fq
