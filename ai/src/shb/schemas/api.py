"""API request/response schemas."""

from typing import Any

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """Request to register a new user."""

    email: str


class UserResponse(BaseModel):
    """Response model for user details."""

    id: str
    email: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class RegisterResponse(UserResponse):
    """Response from registration, including the one-time API key.

    The API key is shown only once at creation; only its hash is stored.
    """

    api_key: str


class PluginMetaResponse(BaseModel):
    """Response model for plugin metadata."""

    id: str
    name: str
    description: str
    version: str
    is_async: bool
    accepts_file: bool
    file_types: list[str]
    input_schema: dict[str, Any] | None


class PluginRunRequest(BaseModel):
    """Request to run a plugin."""

    input: dict[str, Any]


class PluginRunResponse(BaseModel):
    """Response from synchronous plugin run."""

    result: dict[str, Any]


class PluginRunAsyncResponse(BaseModel):
    """Response from asynchronous plugin run."""

    job_id: str
    status: str = "pending"


class JobResponse(BaseModel):
    """Response model for job status."""

    id: str
    plugin_id: str
    status: str
    input: dict
    result: dict | None
    error: str | None
    progress: int
    created_at: str
    started_at: str | None
    finished_at: str | None

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """Response model for file upload."""

    id: str
    original_name: str
    content_type: str
    size_bytes: int
    created_at: str

    class Config:
        from_attributes = True
