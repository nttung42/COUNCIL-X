"""Shared dependencies for API endpoints."""

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shb.core.db import get_db
from shb.db.models import User

_DEFAULT_USER_EMAIL = "default@local"


async def get_default_user(db: AsyncSession = Depends(get_db)) -> User:
    """Return the single shared system user, creating it on first use.

    The API has no per-caller authentication; every job/file is attributed to
    this one user so the existing ``user_id`` foreign keys stay populated.
    """
    user = await db.scalar(select(User).where(User.email == _DEFAULT_USER_EMAIL))
    if user:
        return user

    user = User(email=_DEFAULT_USER_EMAIL, api_key_hash="")
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        user = await db.scalar(select(User).where(User.email == _DEFAULT_USER_EMAIL))
    else:
        await db.refresh(user)
    return user
