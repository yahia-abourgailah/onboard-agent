from langchain_core.messages import BaseMessage, SystemMessage

from onboard_agent.graph.state import AgentState
from onboard_agent.model.llm import get_llm_with_tools
from onboard_agent.prompts.llm_prompt import SYSTEM_PROMPT


def call_llm(state: AgentState) -> dict[str, list[BaseMessage]]:
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    # Resolve the tool-bound model lazily (see model/llm.py) so importing the graph
    # never requires credentials — only actually calling the node does.
    response = get_llm_with_tools().invoke(messages)
    return {"messages": [response]}
