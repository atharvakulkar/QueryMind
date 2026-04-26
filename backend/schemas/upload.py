"""Pydantic models for the dataset upload endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColumnDetail(BaseModel):
    """Column name and PostgreSQL type."""

    name: str
    pg_type: str


class UploadResponse(BaseModel):
    """Returned after a successful CSV upload."""

    schema_name: str = Field(description="PostgreSQL schema (always 'uploads').")
    table_name: str = Field(description="Sanitized table name.")
    fully_qualified: str = Field(description="schema.table identifier.")
    row_count: int = Field(ge=0)
    columns: list[ColumnDetail]
    message: str = Field(default="Dataset uploaded successfully.")


class UploadedTableInfo(BaseModel):
    """Compact info for listing uploaded datasets."""

    table_name: str
    column_count: int
