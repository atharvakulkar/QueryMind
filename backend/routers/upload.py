"""Router for dataset uploads."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.dependencies import ConnectionManagerDep, SettingsDep
from backend.schemas.upload import UploadedTableInfo, UploadResponse
from backend.services.csv_uploader import CsvUploader
from core.exceptions import DataUploadError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Dataset Upload"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a CSV dataset",
)
async def upload_dataset(
    settings: SettingsDep,
    cm: ConnectionManagerDep,
    file: UploadFile = File(...),
) -> UploadResponse:
    """Read a CSV file, infer Schema, and CREATE TABLE + bulk insert rows."""
    if not settings.allow_data_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dataset upload is disabled by configuration (ALLOW_DATA_UPLOAD=false).",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are supported.",
        )

    # Validate file size
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({size_mb:.1f} MB) exceeds maximum allowed ({settings.max_upload_size_mb} MB).",
        )

    uploader = CsvUploader(cm)
    try:
        result = await uploader.upload(file_bytes, file.filename)
    except DataUploadError as exc:
        # Re-raise to let the global exception handler format it as a QueryMindError
        raise exc
    except Exception as exc:
        logger.exception("Unexpected error during CSV upload.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during upload.",
        ) from exc

    return UploadResponse(
        schema_name=result.schema_name,
        table_name=result.table_name,
        fully_qualified=result.fully_qualified,
        row_count=result.row_count,
        columns=[{"name": c["name"], "pg_type": c["pg_type"]} for c in result.columns],
    )


@router.get(
    "s",
    response_model=list[UploadedTableInfo],
    summary="List uploaded datasets",
)
async def list_uploads(
    settings: SettingsDep,
    cm: ConnectionManagerDep,
) -> list[dict]:
    """List all tables that exist in the uploads schema."""
    if not settings.allow_data_upload:
        return []

    uploader = CsvUploader(cm)
    rows = await uploader.list_uploaded_tables()
    return [{"table_name": r["table_name"], "column_count": r["column_count"]} for r in rows]


@router.delete(
    "s/{table_name}",
    status_code=status.HTTP_200_OK,
    summary="Drop an uploaded dataset",
)
async def delete_upload(
    settings: SettingsDep,
    cm: ConnectionManagerDep,
    table_name: str,
) -> dict:
    """Drop a specific uploaded table."""
    if not settings.allow_data_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dataset upload is disabled by configuration.",
        )

    uploader = CsvUploader(cm)
    try:
        await uploader.drop_table(table_name)
    except DataUploadError as exc:
        raise exc
    return {"success": True}
