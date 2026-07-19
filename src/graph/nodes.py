from langchain_core.messages import BaseMessage, SystemMessage

from graph.state import AgentState
from model.llm import get_llm_with_tools
from prompts.llm_prompt import SYSTEM_PROMPT


def call_llm(state: AgentState) -> dict[str, list[BaseMessage]]:
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    # Resolve the tool-bound model lazily (see model/llm.py) so importing the graph
    # never requires credentials — only actually calling the node does.
    response = get_llm_with_tools().invoke(messages)
    return {"messages": [response]}
