from pathlib import Path

import asyncpg

from src.config import settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if settings.database_url:
        _pool = await asyncpg.create_pool(
            settings.database_url, min_size=2, max_size=10
        )


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def run_migrations() -> None:
    pool = await get_pool()
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    sql = migration_file.read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)
