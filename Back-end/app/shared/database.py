# ============================================================
# PaySentinelIQ — Database Engine & Session Factory
# SQLAlchemy 2.0 async with PostgreSQL
# ============================================================

from collections.abc import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.shared.settings import get_settings

settings = get_settings()

# Build connect_args based on the driver (asyncpg vs psycopg)
_db_url = settings.database_url_async
_parsed = urlparse(_db_url)
_is_asyncpg = _parsed.scheme == "postgresql+asyncpg"

_connect_args = {"prepared_statement_cache_size": 0} if _is_asyncpg else {}
if _is_asyncpg:
    _connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    _db_url,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    connect_args=_connect_args,
    # Use NullPool for testing to avoid connection leaks;
    # skip pool_size/max_overflow/pool_timeout — NullPool rejects those kwargs.
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
    **(
        {}
        if settings.ENVIRONMENT == "test"
        else {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        }
    ),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def get_engine() -> AsyncEngine | None:
    """Return the global async engine (lazy-safe accessor).

    Several modules (health checks, background tasks, messaging workers)
    import this accessor instead of the module-level ``engine`` symbol so
    they keep working even if engine creation is deferred or replaced in
    tests.
    """
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the global session factory (used by workers and tasks)."""
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
