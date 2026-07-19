"""Application entrypoint: the FastAPI ASGI app. The database is created and
seeded once on startup via the lifespan handler.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from onboard_agent.api.endpoints import router
from onboard_agent.api.middleware import setup_middleware
from onboard_agent.database.postgres import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="onboard-agent", lifespan=lifespan)
setup_middleware(app)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
