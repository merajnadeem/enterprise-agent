from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings

from app.integrations.database import (
    create_database_pool,
)

from app.api.routes.investigations import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    settings = get_settings()

    app.state.db_pool = await create_database_pool()

    app.state.settings = settings

    try:
        yield

    finally:

        await app.state.db_pool.close()


app = FastAPI(
    title="Enterprise Agentic AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health/live")
async def liveness():

    return {
        "status": "alive"
    }
