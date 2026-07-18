"""Worker process for async job execution."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shb.ai.plugins import AIServiceContext, get_registry
from shb.core.config import get_settings
from shb.db.models import JobStatus
from shb.services.job_service import JobService

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_worker():
    """Main worker loop for processing jobs."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    registry = get_registry()
    registry.discover_and_register()

    logger.info(f"Worker started. Registered {len(registry.list_services())} services.")

    try:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    job_service = JobService(db)
                    pending_jobs = await job_service.get_pending_jobs(limit=1)

                    if not pending_jobs:
                        await asyncio.sleep(settings.job_poll_interval_seconds)
                        continue

                    job = pending_jobs[0]
                    logger.info(f"Processing job {job.id} for service {job.plugin_id}")

                    try:
                        await job_service.update_job_status(job.id, JobStatus.RUNNING)
                        await job_service.commit()

                        service = registry.get(job.plugin_id)
                        if not service:
                            raise ValueError(f"Service {job.plugin_id} not found")

                        def update_progress(progress: int) -> None:
                            """Update job progress synchronously."""

                            async def _update():
                                try:
                                    await job_service.update_job_progress(job.id, progress)
                                    await job_service.commit()
                                except Exception as exc:
                                    logger.warning(f"Failed to update progress: {exc}")

                            try:
                                asyncio.create_task(_update())
                            except Exception as exc:
                                logger.warning(f"Failed to create progress task: {exc}")

                        ctx = AIServiceContext(
                            user_id=job.user_id,
                            service_id=job.plugin_id,
                            job_id=job.id,
                            update_progress=update_progress,
                        )

                        input_data = service.InputSchema(**job.input)
                        result = await service.run(input_data, ctx)

                        await job_service.update_job_status(
                            job.id, JobStatus.COMPLETED, result=result.model_dump()
                        )
                        await job_service.commit()
                        logger.info(f"Job {job.id} completed successfully")

                    except Exception as e:
                        logger.error(f"Job {job.id} failed: {str(e)}", exc_info=True)
                        await job_service.update_job_status(job.id, JobStatus.FAILED, error=str(e))
                        await job_service.commit()

            except Exception as e:
                logger.error(f"Worker error: {str(e)}", exc_info=True)
                await asyncio.sleep(settings.job_poll_interval_seconds)

    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, settings.log_level))
    asyncio.run(run_worker())
