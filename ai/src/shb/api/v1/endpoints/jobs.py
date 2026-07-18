"""API endpoints for job management."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from shb.api.v1.dependencies import get_current_user, get_current_user_sse
from shb.core.db import AsyncSessionLocal, get_db
from shb.db.models import JobStatus, User
from shb.schemas import JobResponse
from shb.services.event_bus import subscribe_job_events
from shb.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

_TERMINAL = {JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value}


def _sse(event: str, data: dict) -> str:
    """Format one Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _terminal_frame(status_value: str, result, error) -> str:
    """Build the closing SSE frame for a finished job."""
    if status_value == JobStatus.COMPLETED.value:
        return _sse("done", {"status": status_value, "result": result})
    return _sse("error", {"status": status_value, "error": error})


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


@router.get("/{job_id}/stream")
async def stream_job(
    job_id: str,
    user: User = Depends(get_current_user_sse),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream a job's progress in real time over SSE (no polling).

    Emits ``snapshot`` (current state) on connect, then ``progress`` events as the
    worker runs, and finally ``done`` (with ``result``) or ``error`` before closing.
    A ``:`` heartbeat comment is sent on idle to keep the connection alive through
    proxies. Auth accepts ``?api_key=`` (for browser ``EventSource``) or the header.
    """
    job = await JobService(db).get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Capture state now — the request-scoped session closes once we return the
    # StreamingResponse; in-loop reads use their own short-lived sessions.
    snap = {
        "status": job.status.value,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
    }

    async def gen():
        yield _sse("snapshot", {"status": snap["status"], "progress": snap["progress"]})
        if snap["status"] in _TERMINAL:
            yield _terminal_frame(snap["status"], snap["result"], snap["error"])
            return

        async for event in subscribe_job_events(job_id):
            if event is None:
                # Idle tick: heartbeat + re-check DB so a missed 'done' still closes us.
                async with AsyncSessionLocal() as s:
                    fresh = await JobService(s).get_job(job_id)
                if fresh and fresh.status.value in _TERMINAL:
                    yield _terminal_frame(fresh.status.value, fresh.result, fresh.error)
                    return
                yield ": heartbeat\n\n"
                continue
            yield _sse(event["type"], event.get("data", {}))
            if event["type"] in ("done", "error"):
                return

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx proxy buffering
        },
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
