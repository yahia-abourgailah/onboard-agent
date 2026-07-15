from langchain_openai import ChatOpenAI
from onboard_agent.config import Settings
settings = Settings()
from onboard_agent.tools import tools


llm = ChatOpenAI(
    model="gemma-4",
    api_key=settings.OPENAI_API_KEY or None,
    base_url=settings.OPENAI_BASE_URL or None,
)
llm_with_tools=llm.bind_tools(tools)
