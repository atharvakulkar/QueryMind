"""Tests for best-effort read-only SQL guards."""

import pytest

from core.exceptions import SQLExecutionError
from database.connection_manager import assert_read_only_select_sql


def test_allows_select() -> None:
    assert_read_only_select_sql("SELECT 1")


def test_allows_with() -> None:
    assert_read_only_select_sql("WITH x AS (SELECT 1 AS n) SELECT n FROM x")


def test_rejects_delete() -> None:
    with pytest.raises(SQLExecutionError) as exc:
        assert_read_only_select_sql("DELETE FROM users")
    assert exc.value.code == "sql_not_allowed"


def test_rejects_chained_statements() -> None:
    with pytest.raises(SQLExecutionError) as exc:
        assert_read_only_select_sql("SELECT 1; DROP TABLE users;")
    assert exc.value.code == "sql_not_allowed"


def test_rejects_insert() -> None:
    with pytest.raises(SQLExecutionError):
        assert_read_only_select_sql("INSERT INTO t VALUES (1)")
