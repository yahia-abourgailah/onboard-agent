"""Tests for the streaming event contract.

The streaming endpoint used to emit text tokens only, discarding every tool
result, which meant a client streaming the reply could never render the floor
map. These pin the behaviour that fixed it.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from graph.build_graph import get_graph, stream_graph_events


def _llm_calling_navigation(destination: str) -> MagicMock:
    """A model that asks for directions on its first turn, then answers."""
    calls = {"n": 0}

    def fake_invoke(_messages: Any) -> AIMessage:
        calls["n"] += 1
        if calls["n"] == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_office_directions",
                        "args": {"destination": destination},
                        "id": "call-1",
                    }
                ],
            )
        return AIMessage(content="HR is on the first floor.")

    model = MagicMock()
    model.invoke.side_effect = fake_invoke
    return model


@pytest.fixture
def _fresh_graph() -> Any:
    get_graph.cache_clear()
    yield
    get_graph.cache_clear()


@patch("graph.nodes.get_llm_with_tools")
def test_stream_emits_floor_map_event(mock_llm: MagicMock, _fresh_graph: None) -> None:
    mock_llm.return_value = _llm_calling_navigation("hr")

    events = list(stream_graph_events("where is HR?", "test-stream-map"))

    maps = [e for e in events if e.get("type") == "floor_map"]
    assert len(maps) == 1, f"expected exactly one floor_map event, got {events}"

    payload = maps[0]
    assert payload["destination"] == "hr"
    assert "/floor-map?highlight=hr" in str(payload["url"])
    assert payload["route"]


@patch("graph.nodes.get_llm_with_tools")
def test_floor_map_arrives_before_the_text_describing_it(
    mock_llm: MagicMock, _fresh_graph: None
) -> None:
    """The map is emitted when the tool runs, which is before the model has
    written the route description — so a client can render it early rather
    than waiting for the reply to finish."""
    mock_llm.return_value = _llm_calling_navigation("hr")

    types = [e.get("type") for e in stream_graph_events("where is HR?", "test-stream-order")]

    assert "floor_map" in types
    assert "token" in types
    assert types.index("floor_map") < types.index("token")


@patch("graph.nodes.get_llm_with_tools")
def test_text_only_reply_emits_no_floor_map(mock_llm: MagicMock, _fresh_graph: None) -> None:
    model = MagicMock()
    model.invoke.return_value = AIMessage(content="Annual leave is 21 days.")
    mock_llm.return_value = model

    events = list(stream_graph_events("how much leave do I get?", "test-stream-plain"))

    assert all(e.get("type") != "floor_map" for e in events)
    assert "".join(str(e["content"]) for e in events if e.get("type") == "token")


@patch("graph.nodes.get_llm_with_tools")
def test_unknown_destination_emits_no_floor_map(mock_llm: MagicMock, _fresh_graph: None) -> None:
    """The tool returns a plain "I don't have directions for X" string for an
    unmapped department (Sales, Marketing, ...). That must not be parsed as a
    map payload."""
    mock_llm.return_value = _llm_calling_navigation("sales")

    events = list(stream_graph_events("where is Sales?", "test-stream-unknown"))

    assert all(e.get("type") != "floor_map" for e in events)


def test_navigation_tool_name_matches_the_registered_tool() -> None:
    """NAVIGATION_TOOL_NAME is compared against ToolMessage.name at runtime; a
    silent rename would drop every map event without failing anything else."""
    from tools import tools
    from tools.navigation_tool import NAVIGATION_TOOL_NAME

    assert NAVIGATION_TOOL_NAME in {t.name for t in tools}
