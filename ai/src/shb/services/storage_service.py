"""Storage service for file management."""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from shb.core.config import get_settings
from shb.db.models import File


class StorageService:
    """Service for managing file storage."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.storage_dir = Path(self.settings.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(
        self, user_id: str, original_name: str, content: bytes, content_type: str
    ) -> File:
        """Save uploaded file and create database record."""
        file_size = len(content)
        if file_size > self.settings.max_file_size_mb * 1024 * 1024:
            raise ValueError(f"File exceeds maximum size of {self.settings.max_file_size_mb}MB")

        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        import uuid

        file_id = str(uuid.uuid4())
        file_path = user_dir / file_id
        file_path.write_bytes(content)

        file_record = File(
            user_id=user_id,
            original_name=original_name,
            stored_path=str(file_path),
            content_type=content_type,
            size_bytes=file_size,
        )
        self.db.add(file_record)
        await self.db.flush()
        return file_record

    async def get_file(self, file_id: str) -> File | None:
        """Get file record by ID."""
        return await self.db.get(File, file_id)

    async def read_file(self, file_path: str) -> bytes:
        """Read file content from storage."""
        return Path(file_path).read_bytes()

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from storage and database."""
        file = await self.get_file(file_id)
        if not file:
            return False

        try:
            Path(file.stored_path).unlink(missing_ok=True)
            await self.db.delete(file)
            await self.db.flush()
            return True
        except Exception:
            return False

    async def commit(self) -> None:
        """Commit pending changes."""
        await self.db.commit()
