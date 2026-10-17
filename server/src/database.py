"""Async MySQL engine, session factory, and idempotent schema bootstrap."""

from collections.abc import AsyncIterator
import re

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


def _database_url(database: str | None) -> URL:
    return URL.create(
        drivername="mysql+asyncmy",
        username=settings.mysql_user,
        password=settings.mysql_password,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=database,
        query={"charset": "utf8mb4"},
    )


if not re.fullmatch(r"[A-Za-z0-9_]+", settings.mysql_database):
    raise RuntimeError("MYSQL_DATABASE may only contain letters, numbers, and underscores")


engine = create_async_engine(
    _database_url(settings.mysql_database),
    echo=settings.mysql_echo,
    pool_pre_ping=True,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def bootstrap_database() -> None:
    """Create the configured database and all ORM tables when absent."""
    bootstrap_engine = create_async_engine(
        _database_url(None),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        async with bootstrap_engine.connect() as connection:
            await connection.exec_driver_sql(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        await bootstrap_engine.dispose()

    # Import model modules before create_all so their tables are registered.
    from src.models import note as _note  # noqa: F401
    from src.models import conversation as _conversation  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    await engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
