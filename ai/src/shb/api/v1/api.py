"""Aggregate API routers for v1."""

from fastapi import APIRouter

from shb.api.v1.endpoints import auth, files, jobs, plugins

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(plugins.router)
api_router.include_router(jobs.router)
api_router.include_router(files.router)
