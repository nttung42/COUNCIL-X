"""Auth endpoints: register, me.

Authentication is API-key based. On registration a user is created and a
plaintext API key is returned exactly once; only its SHA-256 hash is stored.
Authenticated requests pass the key via the ``X-API-Key`` header (see
:func:`shb.api.v1.dependencies.get_current_user`).
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shb.api.v1.dependencies import get_current_user
from shb.core.db import get_db
from shb.core.security import hash_api_key
from shb.db.models import User
from shb.schemas import RegisterRequest, RegisterResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    """Register a new user and issue a one-time API key."""
    email = body.email.strip().lower()

    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    api_key = secrets.token_urlsafe(32)
    user = User(email=email, api_key_hash=hash_api_key(api_key))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        api_key=api_key,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )
