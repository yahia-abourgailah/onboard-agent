"""Application entrypoint.

Resolves the merge between the two `main.py` versions — one that ran the graph
from a `__main__` script, one that served the FastAPI app — into a single ASGI
app. The employee directory DB is initialized once on startup via lifespan.
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
    # FIX (FIX-4): seed/create the directory DB once at startup instead of inside a
    # __main__ block that only ran when the file was executed directly. Uses the
    # modern lifespan handler rather than the deprecated @app.on_event("startup").
    init_db()
    yield


app = FastAPI(title="onboard-agent", lifespan=lifespan)
setup_middleware(app)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
