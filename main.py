"""Application entrypoint: the FastAPI ASGI app. The database is created and
seeded once on startup via the lifespan handler.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

import uvicorn
from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

router = import_module("api.endpoints").router
setup_middleware = import_module("api.middleware").setup_middleware
init_db = import_module("database.postgres").init_db
checkpointer = import_module("memory.checkpointer").checkpointer
get_vector_store = import_module("vectorstore.creation").get_vector_store
get_graph = import_module("graph.build_graph").get_graph


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    checkpointer.setup()
    get_vector_store()
    get_graph()
    yield


app = FastAPI(title="onboard-agent", lifespan=lifespan)
setup_middleware(app)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
