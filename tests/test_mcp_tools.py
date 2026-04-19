"""Unit tests for MCP tool argument validation."""

import pytest

from mcp_server.tools import validate_identifier


def test_validate_identifier_accepts_public() -> None:
    assert validate_identifier("public", "schema_name") == "public"


def test_validate_identifier_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        validate_identifier("public;", "schema_name")
