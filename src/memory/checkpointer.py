"""Checkpointer factory.

MemorySaver keeps state in-process (fine for dev/single-worker). Swap for
PostgresSaver in production so state survives restarts and works across
multiple workers.
"""

from langgraph.checkpoint.memory import MemorySaver

# Module-level singleton: must be the SAME instance every time the graph
# is invoked, or "memory" resets on every call.
checkpointer = MemorySaver()
