from langchain_openai import ChatOpenAI

from onboard_agent.config import Settings

settings = Settings()


llm = ChatOpenAI(
    model="gemma-4",
    api_key=settings.OPENAI_API_KEY or None,
    base_url=settings.OPENAI_BASE_URL or None,
)
