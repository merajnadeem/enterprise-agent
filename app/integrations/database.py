import asyncpg

from app.config import get_settings


async def create_database_pool():

    settings = get_settings()

    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )

    return pool
