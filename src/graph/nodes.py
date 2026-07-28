import logging

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from graph.guardrails import check_prompt_injection_history
from graph.state import AgentState
from model.llm import get_llm_with_tools
from prompts.llm_prompt import SYSTEM_PROMPT

logger = logging.getLogger("onboard_agent")

REFUSAL_MESSAGE = (
    "I can't process that message as written. I can help with onboarding "
    "questions about company policy, floors/departments, or your mentor — "
    "try rephrasing your question."
)


def input_guard(state: AgentState) -> dict[str, object]:
    """Screens BOTH the latest human message and everything checkpointed so
    far for this thread, BEFORE any of it reaches the LLM or a tool.

    Scanning full history (not just the new turn) matters because the
    checkpointer persists messages across calls — a payload smuggled into an
    earlier turn ("remember this for later: ignore all instructions...")
    would otherwise sit dormant until a later turn's context "activates" it,
    slipping past a fresh-input-only check.
    """
    messages = state["messages"]
    human_texts = [
        m.content for m in messages if isinstance(m, HumanMessage) and isinstance(m.content, str)
    ]

    result = check_prompt_injection_history(human_texts)

    if result.flagged:
        logger.warning(
            "prompt_injection_blocked category=%s pattern=%s",
            result.category,
            result.matched_pattern,
        )
        return {
            "messages": [AIMessage(content=REFUSAL_MESSAGE)],
            "injection_flagged": True,
        }

    return {"injection_flagged": False}


def call_llm(state: AgentState) -> dict[str, list[BaseMessage]]:
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = get_llm_with_tools().invoke(messages)
    return {"messages": [response]}
