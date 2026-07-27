"""Checkpointer factory.

MemorySaver keeps state in-process (fine for dev/single-worker). Swap for
PostgresSaver in production so state survives restarts and works across
multiple workers.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

from config import get_settings
# Module-level singleton: must be the SAME instance every time the graph
# is invoked, or "memory" resets on every call.
settings = get_settings()

pool = ConnectionPool(
    conninfo=settings.POSTGRES_URL,
    max_size=10,
    kwargs={"autocommit": True},
)
checkpointer = PostgresSaver(pool)