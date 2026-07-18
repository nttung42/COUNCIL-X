"""Database initialization and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from shb.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Dependency for database session injection."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialize database on startup.

    Creates all tables and seeds a default admin user on first run so that
    the API key shown in the README (``your-api-key``) works immediately.
    """
    import hashlib

    from sqlalchemy import select

    from shb.db.models import Base, User

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default user if the users table is empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is None:
            default_key = "your-api-key"
            default_user = User(
                email="admin@shb.local",
                api_key_hash=hashlib.sha256(default_key.encode()).hexdigest(),
                is_active=True,
            )
            session.add(default_user)
            await session.commit()
            print(
                f"✓ Seeded default user: admin@shb.local  |  X-API-Key: {default_key}",
                flush=True,
            )
