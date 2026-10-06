# ============================================================
# PaySentinelIQ — Alembic Environment Configuration
# Async migration runner for SQLAlchemy 2.0
# ============================================================

import asyncio
from logging.config import fileConfig
from urllib.parse import urlparse

import alembic.context as context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.shared.base_model import Base
from app.shared.settings import get_settings

settings = get_settings()

config = context.config
# Use asyncpg URL for async migrations (alembic uses async_engine_from_config)
db_url = settings.database_url_async
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Build connect_args based on the driver (asyncpg vs psycopg)
    _parsed = urlparse(db_url)
    _is_asyncpg = _parsed.scheme == "postgresql+asyncpg"
    _connect_args = {"prepared_statement_cache_size": 0} if _is_asyncpg else {}
    if _is_asyncpg:
        _connect_args["statement_cache_size"] = 0

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
