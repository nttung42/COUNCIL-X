"""API endpoints for service management."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shb.ai.plugins import AIServiceContext, get_registry
from shb.api.v1.dependencies import get_current_user
from shb.core.celery_app import celery_app
from shb.core.db import get_db
from shb.db.models import User
from shb.schemas import (
    PluginMetaResponse,
    PluginRunAsyncResponse,
    PluginRunRequest,
    PluginRunResponse,
)
from shb.services.job_service import JobService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[PluginMetaResponse])
async def list_services() -> list[PluginMetaResponse]:
    """List available services with metadata."""
    registry = get_registry()
    logger.info(f"list_services called. Services before: {len(registry.services)}")

    # Always ensure services are discovered
    if len(registry.services) == 0:
        logger.info("Discovering services...")
        registry.discover_and_register()
        logger.info(f"Services after discovery: {len(registry.services)}")

    services = registry.list_services()
    logger.info(f"Returning {len(services)} services")

    return [
        PluginMetaResponse(
            id=service.id,
            name=service.name,
            description=service.description,
            version=service.version,
            is_async=service.is_async,
            accepts_file=service.accepts_file,
            file_types=service.file_types,
            input_schema=registry.get_service_schema(service.id),
        )
        for service in services
    ]


@router.get("/{service_id}", response_model=PluginMetaResponse)
async def get_service(service_id: str) -> PluginMetaResponse:
    """Get details for a specific service."""
    registry = get_registry()

    # Discover services if not already discovered
    if not registry.services:
        registry.discover_and_register()

    service = registry.get(service_id)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    return PluginMetaResponse(
        id=service.meta.id,
        name=service.meta.name,
        description=service.meta.description,
        version=service.meta.version,
        is_async=service.meta.is_async,
        accepts_file=service.meta.accepts_file,
        file_types=service.meta.file_types,
        input_schema=registry.get_service_schema(service_id),
    )


@router.post("/{service_id}/run", status_code=200)
async def run_service(
    service_id: str,
    request: PluginRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PluginRunResponse | PluginRunAsyncResponse:
    """Run a service with the provided input."""
    registry = get_registry()

    # Discover services if not already discovered
    if not registry.services:
        registry.discover_and_register()

    service = registry.get(service_id)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_id}' not found",
        )

    try:
        input_data = service.InputSchema(**request.input)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )

    if service.meta.is_async:
        job_service = JobService(db)
        job = await job_service.create_job(user.id, service_id, request.input)
        await job_service.commit()

        task = celery_app.send_task(
            "shb.workers.tasks.execute_job",
            args=[job.id, user.id, service_id, request.input],
            queue="default",
        )

        await job_service.set_celery_task_id(job.id, task.id)
        await job_service.commit()

        return PluginRunAsyncResponse(job_id=job.id, status="pending")
    else:
        ctx = AIServiceContext(user_id=user.id, service_id=service_id)
        result = await service.run(input_data, ctx)

        return PluginRunResponse(result=result.model_dump())
