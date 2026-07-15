from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from onboard_agent.graph.nodes import call_llm
from onboard_agent.graph.state import AgentState
from onboard_agent.tools import tools


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "llm")
    graph_builder.add_conditional_edges("llm", tools_condition)  # -> "tools" or END
    graph_builder.add_edge("tools", "llm")

    return graph_builder.compile()


def invoke_graph(question: str):
    graph = build_graph()
    return graph.invoke({"messages": [{"role": "user", "content": question}]})
