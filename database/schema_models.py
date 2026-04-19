"""Pydantic models describing PostgreSQL schema metadata."""

from pydantic import BaseModel, Field


class ForeignKeyInfo(BaseModel):
    """Single foreign key reference."""

    constraint_name: str
    column_name: str
    referenced_schema: str
    referenced_table: str
    referenced_column: str


class ColumnInfo(BaseModel):
    """Column metadata from information_schema."""

    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int = Field(ge=1)


class TableInfo(BaseModel):
    """Table with columns and optional foreign keys."""

    schema_name: str
    name: str
    table_type: str = "BASE TABLE"
    columns: list[ColumnInfo] = Field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    """Full introspected schema snapshot."""

    tables: list[TableInfo] = Field(default_factory=list)
