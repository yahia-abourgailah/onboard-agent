"""Shared test fixtures.

Patches the module-level Postgres checkpointer with an in-memory one for the
whole test session, so graph-level tests (test_input_guard.py etc.) run
without a live Postgres instance. Production code is untouched — this only
affects what `graph.build_graph` sees when it imports `checkpointer`.
"""

from collections.abc import Generator

import pytest
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture(autouse=True)
def _use_memory_checkpointer(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    memory_checkpointer = MemorySaver()
    # build_graph.py does `from memory.checkpointer import checkpointer` at
    # import time, so patch it where it's *used*, not where it's defined.
    monkeypatch.setattr("graph.build_graph.checkpointer", memory_checkpointer)
    yield
