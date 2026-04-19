"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, PostgresDsn, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.exceptions import ConfigError


class Settings(BaseSettings):
    """Central configuration; all secrets and URLs come from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="QueryMind", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: PostgresDsn = Field(..., alias="DATABASE_URL")
    allow_adhoc_sql: bool = Field(default=False, alias="ALLOW_ADHOC_SQL")
    max_query_rows: int = Field(default=500, ge=1, le=10_000, alias="MAX_QUERY_ROWS")
    statement_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        alias="STATEMENT_TIMEOUT_SECONDS",
    )
    # Groq / agent (Phase 3)
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        alias="GROQ_MODEL",
    )
    agent_max_retries: int = Field(default=3, ge=1, le=10, alias="AGENT_MAX_RETRIES")
    log_agent_sql: bool = Field(
        default=True,
        alias="LOG_AGENT_SQL",
        description="Log generated SQL (disable in production if prompts may contain secrets).",
    )
    mcp_server_cwd: str | None = Field(
        default=None,
        alias="MCP_SERVER_CWD",
        description="Working directory for MCP stdio subprocess (default: cwd).",
    )

    @field_validator("log_level")
    @classmethod
    def log_level_upper(cls, v: str) -> str:
        return v.upper()


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton suitable for dependency injection."""
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigError(
            "Failed to load configuration. Check required environment variables.",
            details={"errors": exc.errors()},
        ) from exc
