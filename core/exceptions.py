"""Domain exceptions for QueryMind."""


class QueryMindError(Exception):
    """Base error for API-safe messaging and logging."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "querymind_error",
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ConfigError(QueryMindError):
    """Invalid or missing configuration."""

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code="config_error", details=details)


class DatabaseConnectionError(QueryMindError):
    """Pool acquisition or connectivity failures."""

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code="database_connection_error", details=details)


class SQLExecutionError(QueryMindError):
    """SQL rejected or failed at execution time."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "sql_execution_error",
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)


class SchemaLinkingError(QueryMindError):
    """Schema linking failed validation or could not be grounded."""

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code="schema_linking_error", details=details)


class SQLGenerationError(QueryMindError):
    """LLM failed to produce valid SQL after retries."""

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code="sql_generation_error", details=details)


class MCPConnectionError(QueryMindError):
    """Could not connect to or use the MCP schema server."""

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code="mcp_connection_error", details=details)
