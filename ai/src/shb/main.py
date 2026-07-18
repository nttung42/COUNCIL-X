"""FastAPI application entry point for SHB AI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shb.ai.plugins import get_registry
from shb.api.v1.api import api_router
from shb.core.db import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the FastAPI app."""
    try:
        print("🚀 Starting SHB AI...", flush=True)
        await init_db()
        print("✓ Database initialized", flush=True)

        # Discover and register AI services
        registry = get_registry()
        registry.discover_and_register()
        services = registry.list_services()
        service_ids = [s.id for s in services]
        print(f"✓ Registered {len(services)} AI services: {service_ids}", flush=True)
        logger.info(f"Registered {len(services)} AI services: {service_ids}")
    except Exception as e:
        print(f"❌ Startup error: {e}", flush=True)
        raise

    yield

    # Cleanup if needed
    print("🛑 Shutting down SHB AI", flush=True)


app = FastAPI(
    title="SHB AI",
    description="A unified platform for multiple AI tools",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
