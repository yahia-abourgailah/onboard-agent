"""Checkpointer factory.

MemorySaver keeps state in-process (fine for dev/single-worker). Swap for
PostgresSaver in production so state survives restarts and works across
multiple workers.
"""

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from config import get_settings

# Module-level singleton: must be the SAME instance every time the graph
# is invoked, or "memory" resets on every call.
settings = get_settings()

pool = ConnectionPool(
    conninfo=settings.POSTGRES_URL,
    max_size=10,
    kwargs={"autocommit": True, "row_factory": dict_row},
    connection_class=Connection[DictRow],
)
checkpointer = PostgresSaver(pool)
