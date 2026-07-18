"""Shared dependencies for API endpoints."""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.core.db import get_db
from shb.db.models import User


async def get_current_user(
    api_key: str = Header(..., alias="X-API-Key"), db: AsyncSession = Depends(get_db)
) -> User:
    """Verify API key and return authenticated user."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    import hashlib

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
