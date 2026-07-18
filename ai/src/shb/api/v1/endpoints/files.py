"""API endpoints for file management."""

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse as PhysicalFileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shb.api.v1.dependencies import get_default_user
from shb.core.db import get_db
from shb.db.models import User
from shb.schemas import FileResponse
from shb.services.storage_service import StorageService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_default_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Upload a file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename required",
        )

    try:
        content = await file.read()
        storage_service = StorageService(db)
        file_record = await storage_service.save_upload(
            user.id,
            file.filename,
            content,
            file.content_type or "application/octet-stream",
        )
        await storage_service.commit()

        return FileResponse(
            id=file_record.id,
            original_name=file_record.original_name,
            content_type=file_record.content_type,
            size_bytes=file_record.size_bytes,
            created_at=file_record.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


async def _file_response(file_id: str, db: AsyncSession, disposition: str) -> PhysicalFileResponse:
    storage_service = StorageService(db)
    file_record = await storage_service.get_file(file_id)

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if not os.path.exists(file_record.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file missing from storage — it may have been deleted",
        )

    return PhysicalFileResponse(
        path=file_record.stored_path,
        filename=file_record.original_name,
        media_type=file_record.content_type,
        content_disposition_type=disposition,
    )


@router.get("/{file_id}/preview", summary="Preview a file inline by ID")
async def preview_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> PhysicalFileResponse:
    """Return file bytes inline so browser preview widgets do not trigger download."""
    return await _file_response(file_id, db, "inline")


@router.get("/{file_id}/download", summary="Download a file by ID")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> PhysicalFileResponse:
    """Download the physical file associated with *file_id*."""
    return await _file_response(file_id, db, "attachment")
