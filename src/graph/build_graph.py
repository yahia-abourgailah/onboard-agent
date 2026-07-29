from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from graph.nodes import call_llm, input_guard
from graph.state import AgentState
from memory.checkpointer import checkpointer
from tools import tools
from tools.navigation_tool import NAVIGATION_TOOL_NAME, parse_floor_map

load_dotenv()  # Loads variables from .env


# Typed as the Runnable interface the compiled graph exposes (invoke). This stays
# stable across langgraph versions, unlike CompiledStateGraph's generic arity.
def _route_after_guard(state: AgentState) -> str:
    return END if state.get("injection_flagged") else "llm"


@lru_cache(maxsize=1)
def get_graph() -> Runnable[Any, Any]:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("input_guard", input_guard)
    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "input_guard")
    graph_builder.add_conditional_edges("input_guard", _route_after_guard, {"llm": "llm", END: END})
    graph_builder.add_conditional_edges("llm", tools_condition)
    graph_builder.add_edge("tools", "llm")

    return graph_builder.compile(checkpointer=checkpointer)


def invoke_graph(question: str, thread_id: str) -> dict[str, Any]:
    config = RunnableConfig(configurable={"thread_id": thread_id})
    # Only pass the NEW message — the checkpointer restores everything before it.
    result: dict[str, Any] = get_graph().invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return result


def stream_graph_events(question: str, thread_id: str) -> Iterator[dict[str, object]]:
    """Yield streamable events from the agent graph.

    Two kinds come out:
      {"type": "token", "content": ...}  incremental text of the reply
      {"type": "floor_map", ...}         the navigation tool's map payload,
                                         identical to /chat's `floor_map`

    The tool result is emitted as soon as the tool runs, which is *before* the
    model has finished describing the route — so a client can render the map
    while the surrounding text is still arriving.
    """
    config = RunnableConfig(configurable={"thread_id": thread_id})
    for chunk, metadata in get_graph().stream(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
        stream_mode="messages",
    ):
        node = metadata.get("langgraph_node")

        if node == "tools":
            if (
                isinstance(chunk, ToolMessage)
                and chunk.name == NAVIGATION_TOOL_NAME
                and isinstance(chunk.content, str)
            ):
                payload = parse_floor_map(chunk.content)
                if payload is not None:
                    yield payload
            continue

        if node != "llm":
            continue

        content = chunk.content
        if isinstance(content, str) and content:
            yield {"type": "token", "content": content}
