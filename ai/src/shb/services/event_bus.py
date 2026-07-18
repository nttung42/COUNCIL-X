"""Redis pub/sub event bus for streaming job progress to SSE clients.

The Celery worker :func:`publish_job_event` (sync) each time a job's progress or
status changes; the FastAPI SSE endpoint :func:`subscribe_job_events` (async)
relays those events to the browser over ``text/event-stream``. Decoupling via
Redis pub/sub means the API process streams live progress produced by a *separate*
worker process without polling the DB.

Events are JSON ``{"type": <progress|status|done|error>, "data": {...}}`` on the
channel ``job-events:{job_id}``.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import redis
import redis.asyncio as aioredis

from shb.core.config import get_settings

logger = logging.getLogger(__name__)


def channel(job_id: str) -> str:
    """Redis pub/sub channel carrying one job's events."""
    return f"job-events:{job_id}"


def publish_job_event(job_id: str, event_type: str, data: dict[str, Any] | None = None) -> None:
    """Publish a job event to Redis (synchronous — safe from the Celery worker).

    Never raises: a pub/sub failure must not fail the job it is reporting on.
    """
    payload = json.dumps({"type": event_type, "data": data or {}})
    try:
        client = redis.Redis.from_url(get_settings().celery_broker_url)
        client.publish(channel(job_id), payload)
        client.close()
    except Exception as exc:  # noqa: BLE001 - telemetry must never break the job
        logger.warning("publish_job_event(%s, %s) failed: %s", job_id, event_type, exc)


async def subscribe_job_events(
    job_id: str, *, idle_timeout: float = 15.0
) -> AsyncIterator[dict | None]:
    """Yield each job event as a dict; yield ``None`` on idle timeout (heartbeat tick).

    The ``None`` ticks let the SSE endpoint emit a heartbeat comment (keeping the
    connection alive through proxies) and re-check the DB for a terminal state.
    """
    client = aioredis.from_url(get_settings().celery_broker_url)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel(job_id))
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=idle_timeout)
            if msg is None:
                yield None  # idle → heartbeat
                continue
            data = msg.get("data")
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            try:
                yield json.loads(data)
            except (TypeError, ValueError):
                logger.debug("dropping malformed job event: %r", data)
    finally:
        try:
            await pubsub.unsubscribe(channel(job_id))
            await pubsub.aclose()
            await client.aclose()
        except Exception:  # noqa: BLE001 - best-effort cleanup
            logger.debug("pubsub cleanup failed for %s", job_id, exc_info=True)
