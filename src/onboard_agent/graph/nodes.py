from langchain_core.messages import SystemMessage

from onboard_agent.graph.state import AgentState
from onboard_agent.model.llm import llm_with_tools
from onboard_agent.prompts.llm_prompt import SYSTEM_PROMPT


def call_llm(state: AgentState) -> dict:
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
