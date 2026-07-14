from langchain_anthropic import ChatAnthropic

from onboard_agent.tools import tools

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
llm_with_tools = llm.bind_tools(tools)
