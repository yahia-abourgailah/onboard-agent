from collections.abc import Iterator
from typing import Any

from dotenv import load_dotenv
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from graph.nodes import call_llm
from graph.state import AgentState
from memory.checkpointer import checkpointer
from tools import tools

load_dotenv()  # Loads variables from .env


# Typed as the Runnable interface the compiled graph exposes (invoke). This stays
# stable across langgraph versions, unlike CompiledStateGraph's generic arity.
def build_graph() -> Runnable[Any, Any]:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "llm")
    graph_builder.add_conditional_edges("llm", tools_condition)  # -> "tools" or END
    graph_builder.add_edge("tools", "llm")

    return graph_builder.compile(checkpointer=checkpointer)


# Build ONCE at import time. If you rebuild the graph per-request, MemorySaver's
# in-memory store effectively gets orphaned/discarded depending on how it's
# referenced — always reuse one compiled graph.
_graph = build_graph()


def invoke_graph(question: str, thread_id: str) -> dict[str, Any]:
    config = RunnableConfig(configurable={"thread_id": thread_id})
    # Only pass the NEW message — the checkpointer restores everything before it.
    result: dict[str, Any] = _graph.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return result


def stream_graph_tokens(question: str, thread_id: str) -> Iterator[str]:
    """Yield LLM text tokens from the agent graph (final assistant reply streams token-by-token)."""
    config = RunnableConfig(configurable={"thread_id": thread_id})
    for chunk, metadata in _graph.stream(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
        stream_mode="messages",
    ):
        if metadata.get("langgraph_node") != "llm":
            continue
        content = chunk.content
        if isinstance(content, str) and content:
            yield content
