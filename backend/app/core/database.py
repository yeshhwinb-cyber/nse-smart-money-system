from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool:
            return
        try:
            import asyncpg
        except ModuleNotFoundError as exc:
            raise RuntimeError("ASYNC_PG_DRIVER_NOT_INSTALLED") from exc
        settings = get_settings()
        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )
        logger.info("PostgreSQL pool connected")

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL pool closed")

    async def acquire(self) -> AsyncIterator[Any]:
        if not self.pool:
            await self.connect()
        assert self.pool is not None
        async with self.pool.acquire() as connection:
            yield connection

    async def ping(self) -> bool:
        if not self.pool:
            await self.connect()
        assert self.pool is not None
        async with self.pool.acquire() as connection:
            value = await connection.fetchval("SELECT 1")
        return value == 1


db = Database()
