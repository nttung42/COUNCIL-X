"""Celery application factory for SHB AI."""

from celery import Celery

from shb.core.celery_config import configure_celery
from shb.core.config import get_settings


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery("shb")
    settings = get_settings()
    return configure_celery(app, settings)


celery_app = create_celery_app()
