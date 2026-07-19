from typing import Any

from langchain_core.runnables import Runnable
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from graph.nodes import call_llm
from graph.state import AgentState
from tools import tools


# Typed as the Runnable interface the compiled graph exposes (invoke). This stays
# stable across langgraph versions, unlike CompiledStateGraph's generic arity.
def build_graph() -> Runnable[Any, Any]:
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "llm")
    graph_builder.add_conditional_edges("llm", tools_condition)  # -> "tools" or END
    graph_builder.add_edge("tools", "llm")

    return graph_builder.compile()


def invoke_graph(question: str) -> dict[str, Any]:
    graph = build_graph()
    result: dict[str, Any] = graph.invoke({"messages": [{"role": "user", "content": question}]})
    return result
