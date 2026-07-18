# syntax=docker/dockerfile:1.7
#
# Multi-stage build for SHB AI:
#   - "base"   : python + dependencies
#   - "api"    : API server stage
#

FROM python:3.12-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Deps layer — caches independently of source code.
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# Source
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]


# ---------------------------------------------------------------------------
# API stage
# ---------------------------------------------------------------------------
FROM base AS api

EXPOSE 8000

CMD ["uvicorn", "shb.main:app", "--host", "0.0.0.0", "--port", "8000"]
