#!/bin/bash
set -e

# Run migrations if needed (convert async database URL to sync for alembic)
if [ -n "$DATABASE_URL" ]; then
    ALEMBIC_DB_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+asyncpg:\/\//postgresql:\/\//')
    export ALEMBIC_DB_URL
    # Try to run migrations, but don't fail if no migrations exist
    ALEMBIC_DB_URL="$ALEMBIC_DB_URL" alembic upgrade head || true
fi

# Execute the passed command
exec "$@"
