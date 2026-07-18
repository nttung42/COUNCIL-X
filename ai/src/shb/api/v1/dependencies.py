"""Shared dependencies for API endpoints."""

import hashlib

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.core.db import get_db
from shb.db.models import User


async def _user_for_key(api_key: str | None, db: AsyncSession) -> User:
    """Resolve an active user from a plaintext API key, or raise 401."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    result = await db.execute(
        select(User).where(User.api_key_hash == hashlib.sha256(api_key.encode()).hexdigest())
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return user


async def get_current_user(
    api_key: str = Header(..., alias="X-API-Key"), db: AsyncSession = Depends(get_db)
) -> User:
    """Verify API key (``X-API-Key`` header) and return the authenticated user."""
    return await _user_for_key(api_key, db)


async def get_current_user_sse(
    api_key_query: str | None = Query(default=None, alias="api_key"),
    api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Auth for SSE endpoints.

    Browser ``EventSource`` cannot set headers, so accept the key via the
    ``?api_key=`` query parameter as well as the ``X-API-Key`` header.
    """
    return await _user_for_key(api_key_query or api_key_header, db)
