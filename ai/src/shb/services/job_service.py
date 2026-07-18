"""Job service for async task management."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.db.models import Job, JobStatus


class JobService:
    """Service for managing async jobs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(
        self,
        user_id: str,
        plugin_id: str,
        input_data: dict[str, Any],
        input_file_path: str | None = None,
    ) -> Job:
        """Create a new job."""
        job = Job(
            user_id=user_id,
            plugin_id=plugin_id,
            input=input_data,
            input_file_path=input_file_path,
            status=JobStatus.PENDING,
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        return await self.db.get(Job, job_id)

    async def list_user_jobs(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> tuple[list[Job], int]:
        """List jobs for a user with pagination."""
        query = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        total = await self.db.scalar(select(func.count(Job.id)).where(Job.user_id == user_id))
        result = await self.db.execute(query.limit(limit).offset(offset))
        return result.scalars().all(), total or 0

    async def update_job_status(
        self, job_id: str, status: JobStatus, result: dict | None = None, error: str | None = None
    ) -> Job | None:
        """Update job status."""
        job = await self.get_job(job_id)
        if not job:
            return None

        job.status = status
        if status == JobStatus.RUNNING:
            job.started_at = datetime.now(UTC)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.finished_at = datetime.now(UTC)

        if result is not None:
            job.result = result
        if error is not None:
            job.error = error

        await self.db.flush()
        return job

    async def update_job_progress(self, job_id: str, progress: int) -> Job | None:
        """Update job progress."""
        job = await self.get_job(job_id)
        if job:
            job.progress = min(100, max(0, progress))
            await self.db.flush()
        return job

    async def get_pending_jobs(self, limit: int = 10) -> list[Job]:
        """Get pending jobs for processing."""
        query = (
            select(Job).where(Job.status == JobStatus.PENDING).order_by(Job.created_at).limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def cancel_job(self, job_id: str) -> Job | None:
        """Cancel a pending job."""
        job = await self.get_job(job_id)
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            job.finished_at = datetime.now(UTC)
            await self.db.flush()
            return job
        return None

    async def commit(self) -> None:
        """Commit pending changes."""
        await self.db.commit()

    async def refresh(self, job: Job) -> None:
        """Refresh job from database."""
        await self.db.refresh(job)

    async def set_celery_task_id(self, job_id: str, celery_task_id: str) -> Job | None:
        """Associate Celery task ID with job."""
        job = await self.get_job(job_id)
        if job:
            job.celery_task_id = celery_task_id
            await self.db.flush()
        return job
