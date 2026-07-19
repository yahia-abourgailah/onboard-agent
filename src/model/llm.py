"""LLM factory.

The base model and the tool-bound model are built lazily (lru_cache) so importing
this module never requires credentials — ChatOpenAI validates the key on
construction. Each is a single shared instance, created on first use.
"""

from functools import lru_cache

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from config import Settings
from tools import tools


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
    """Tool-bound model so the agent node can emit tool calls."""
    return get_llm().bind_tools(tools)
