"""LLM factory.

Both the base model and the tool-bound model are built lazily. Constructing a
ChatOpenAI validates credentials immediately, so building at import time crashed
every import on a machine without a key (tests, the graph, app startup). The
lru_cache keeps each a single shared instance, created on first use.
"""

from functools import lru_cache

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from onboard_agent.config import Settings
from onboard_agent.tools import tools


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """Base chat model, pointed at an OpenAI-compatible endpoint (vLLM in prod)."""
    settings = Settings()
    return ChatOpenAI(
        model="gemma-4",
        # ChatOpenAI expects a SecretStr; wrap only when a key is actually set so a
        # keyless local vLLM (which ignores auth) still works.
        api_key=SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None,
        base_url=settings.OPENAI_BASE_URL or None,
    )


@lru_cache(maxsize=1)
def get_llm_with_tools() -> Runnable[LanguageModelInput, BaseMessage]:
    # FIX (FIX-1): the agent node referenced `llm_with_tools`, which was never
    # defined — so importing the graph raised ImportError and dev did not run.
    # Bind the tools here so the model can emit tool calls.
    return get_llm().bind_tools(tools)
