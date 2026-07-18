"""Alembic environment script."""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from shb.core.config import Settings
from shb.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_database_url() -> str:
    """Resolve the migration DB URL from ALEMBIC_DB_URL, else the app's .env-backed Settings."""
    url = os.getenv("ALEMBIC_DB_URL") or Settings().database_url
    # Convert async URL to sync if needed
    return url.replace("postgresql+asyncpg://", "postgresql://")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = _get_database_url()

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
