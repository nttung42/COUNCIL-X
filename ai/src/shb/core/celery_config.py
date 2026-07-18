"""Celery configuration for SHB AI."""

from kombu import Exchange, Queue


def configure_celery(celery_app, settings):
    """Configure Celery with Redis broker and application-specific settings."""
    celery_app.conf.broker_url = settings.celery_broker_url
    celery_app.conf.result_backend = settings.celery_result_backend

    celery_app.conf.broker_connection_retry_on_startup = True
    celery_app.conf.broker_connection_retry = True
    celery_app.conf.broker_connection_max_retries = 10

    # Auto-discover task modules so workers find execute_job on startup
    celery_app.conf.imports = ("shb.workers.tasks",)

    celery_app.conf.task_serializer = "json"
    celery_app.conf.accept_content = ["json"]
    celery_app.conf.result_serializer = "json"

    celery_app.conf.timezone = "UTC"
    celery_app.conf.enable_utc = True

    celery_app.conf.task_acks_late = True
    celery_app.conf.task_reject_on_worker_lost = True
    celery_app.conf.task_track_started = True

    celery_app.conf.task_autoretry_for = (Exception,)
    celery_app.conf.task_max_retries = settings.celery_task_max_retries
    celery_app.conf.task_default_retry_delay = 60

    celery_app.conf.task_soft_time_limit = settings.celery_task_soft_limit
    celery_app.conf.task_time_limit = settings.celery_task_hard_limit

    celery_app.conf.task_routes = {
        "shb.workers.tasks.*": {"queue": "default"},
    }

    celery_app.conf.task_queues = (
        Queue(
            "default",
            exchange=Exchange("default", type="direct"),
            routing_key="default",
            durable=True,
        ),
        Queue(
            "priority",
            exchange=Exchange("priority", type="direct"),
            routing_key="priority",
            durable=True,
        ),
    )

    celery_app.conf.worker_concurrency = settings.celery_worker_concurrency
    celery_app.conf.worker_prefetch_multiplier = 4
    celery_app.conf.worker_max_tasks_per_child = 1000

    celery_app.conf.result_expires = 86400

    celery_app.conf.worker_send_task_events = True
    celery_app.conf.task_send_sent_event = True

    return celery_app
