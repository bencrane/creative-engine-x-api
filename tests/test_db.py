from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src import db


@pytest.fixture(autouse=True)
def reset_pool():
    db._pool = None
    yield
    db._pool = None


def test_migration_sql_is_valid_sql():
    """Verify the migration file exists and contains expected tables."""
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    assert migration_file.exists()
    sql = migration_file.read_text()
    for table in [
        "organizations",
        "api_keys",
        "brand_contexts",
        "generated_artifacts",
        "jobs",
        "landing_page_submissions",
        "usage_events",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


async def test_get_pool_raises_when_not_initialized():
    with pytest.raises(RuntimeError, match="DB pool not initialized"):
        await db.get_pool()


async def test_init_pool_skips_when_no_url():
    with patch.object(db.settings, "database_url", ""):
        await db.init_pool()
    assert db._pool is None


async def test_close_pool_when_none():
    await db.close_pool()  # should not raise


async def test_close_pool_calls_close():
    mock_pool = AsyncMock()
    db._pool = mock_pool
    await db.close_pool()
    mock_pool.close.assert_awaited_once()
    assert db._pool is None


async def test_run_migrations_reads_and_executes():
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    db._pool = mock_pool
    await db.run_migrations()
    mock_conn.execute.assert_awaited_once()
    sql_arg = mock_conn.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS organizations" in sql_arg
