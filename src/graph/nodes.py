import logging

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)

from graph.guardrails import check_prompt_injection
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
    """Screens the newest human message BEFORE it reaches the LLM or a tool,
    and deletes it from the thread if it is flagged.

    Every message is screened exactly once, on arrival, so a payload can never
    reach checkpointed history unscreened — which is what protects against the
    "plant it now, activate it later" attack. Deleting the flagged message is
    what makes screening-on-arrival sufficient: nothing malicious survives in
    history to influence a later turn.

    Do NOT re-scan full history here instead. The flagged text stays in the
    thread, so every later innocent turn re-matches it and is refused, and the
    conversation is bricked until the user starts a new one.
    """
    latest = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if latest is None or not isinstance(latest.content, str):
        return {"injection_flagged": False}

    result = check_prompt_injection(latest.content)

    if not result.flagged:
        return {"injection_flagged": False}

    logger.warning(
        "prompt_injection_blocked category=%s pattern=%s",
        result.category,
        result.matched_pattern,
    )

    # RemoveMessage needs the reducer-assigned id; it is always set for
    # messages that have been through the graph, but stay defensive so a
    # hand-constructed message can still be refused rather than crashing.
    removals: list[BaseMessage] = [RemoveMessage(id=latest.id)] if latest.id else []
    return {
        "messages": [*removals, AIMessage(content=REFUSAL_MESSAGE)],
        "injection_flagged": True,
    }


def call_llm(state: AgentState) -> dict[str, list[BaseMessage]]:
    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = get_llm_with_tools().invoke(messages)
    return {"messages": [response]}
