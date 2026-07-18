"""Security utilities for API key validation."""

import hashlib

from fastapi import Header, HTTPException, status

from shb.core.config import get_settings

settings = get_settings()


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    return x_api_key


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key_hash(api_key: str, api_key_hash: str) -> bool:
    """Verify API key against stored hash."""
    return hash_api_key(api_key) == api_key_hash
