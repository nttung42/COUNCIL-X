"""API endpoints for job management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shb.api.v1.dependencies import get_current_user
from shb.core.db import get_db
from shb.db.models import JobStatus, User
from shb.schemas import JobResponse
from shb.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get job status and results."""
    job_service = JobService(db)
    job = await job_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job",
        )

    return JobResponse(
        id=job.id,
        plugin_id=job.plugin_id,
        status=job.status.value,
        input=job.input,
        result=job.result,
        error=job.error,
        progress=job.progress,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    limit: int = 10,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobResponse]:
    """List user's jobs with pagination."""
    job_service = JobService(db)
    jobs, _ = await job_service.list_user_jobs(user.id, limit=limit, offset=offset)

    return [
        JobResponse(
            id=job.id,
            plugin_id=job.plugin_id,
            status=job.status.value,
            input=job.input,
            result=job.result,
            error=job.error,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
        )
        for job in jobs
    ]


@router.delete("/{job_id}", status_code=204)
async def cancel_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a pending job."""
    job_service = JobService(db)
    job = await job_service.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this job",
        )

    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending jobs",
        )

    await job_service.cancel_job(job_id)
    await job_service.commit()
