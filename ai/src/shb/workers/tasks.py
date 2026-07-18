"""Celery tasks for job execution."""

import asyncio
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shb.ai.plugins import AIServiceContext, get_registry
from shb.core.celery_app import celery_app
from shb.core.config import get_settings
from shb.db.models import JobStatus
from shb.services.event_bus import publish_job_event
from shb.services.job_service import JobService
from shb.services.storage_service import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(
    bind=True,
    name="shb.workers.tasks.execute_job",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def execute_job(self, job_id: str, user_id: str, plugin_id: str, input_data: dict[str, Any]):
    """Execute a job asynchronously using Celery."""
    _masked_db_url = re.sub(r"://([^:]+):[^@]+@", r"://\1:***@", settings.database_url)
    logger.info(
        f"Job {job_id} starting: plugin={plugin_id!r} input={input_data!r} "
        f"db={_masked_db_url!r}"
    )
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _run():
        # Use two separate sessions:
        #   - job_db   → JobService  (status / progress updates)
        #   - store_db → StorageService (file read / write)
        # This prevents asyncpg "another operation is in progress" errors
        # that occur when a single session is used for concurrent operations.
        job_db = AsyncSessionLocal()
        store_db = AsyncSessionLocal()
        try:
            job_service = JobService(job_db)
            storage_service = StorageService(store_db)

            await job_service.update_job_status(job_id, JobStatus.RUNNING)
            await job_service.commit()
            publish_job_event(job_id, "status", {"status": JobStatus.RUNNING.value})

            registry = get_registry()
            if not registry.services:
                registry.discover_and_register()
            service = registry.get(plugin_id)
            if not service:
                raise ValueError(f"Service {plugin_id} not found")

            def update_progress(progress: int) -> None:
                """Publish progress over SSE (sync) and persist it (fire-and-forget)."""
                publish_job_event(job_id, "progress", {"progress": progress})

                async def _update():
                    async with AsyncSessionLocal() as progress_db:
                        try:
                            progress_service = JobService(progress_db)
                            await progress_service.update_job_progress(job_id, progress)
                            await progress_service.commit()
                        except Exception as exc:
                            logger.warning(f"Failed to update progress: {exc}")

                try:
                    asyncio.create_task(_update())
                except Exception as exc:
                    logger.warning(f"Failed to create progress task: {exc}")

            ctx = AIServiceContext(
                user_id=user_id,
                service_id=plugin_id,
                job_id=job_id,
                update_progress=update_progress,
                storage_service=storage_service,  # ← prevents plugin from creating its own engine
                db_session_factory=AsyncSessionLocal,  # ← DB-reading services (property_lookup)
            )

            input_schema = service.InputSchema(**input_data)
            result = await service.run(input_schema, ctx)

            result_payload = result.model_dump()
            await job_service.update_job_status(job_id, JobStatus.COMPLETED, result=result_payload)
            await job_service.commit()
            publish_job_event(
                job_id, "done", {"status": JobStatus.COMPLETED.value, "result": result_payload}
            )
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            try:
                async with AsyncSessionLocal() as err_db:
                    err_service = JobService(err_db)
                    await err_service.update_job_status(job_id, JobStatus.FAILED, error=str(e))
                    await err_service.commit()
                publish_job_event(
                    job_id, "error", {"status": JobStatus.FAILED.value, "error": str(e)}
                )
            except Exception as inner_e:
                logger.error(f"Failed to update job status: {inner_e}")
            raise
        finally:
            await job_db.close()
            await store_db.close()
            await engine.dispose()

    asyncio.run(_run())
