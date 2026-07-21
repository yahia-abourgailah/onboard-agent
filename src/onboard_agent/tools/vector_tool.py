from langchain_core.tools import tool

from onboard_agent.vectorstore.retriever import search_knowledge_base


@tool
def query_vector_db(query: str) -> str:
    """
    Search the company knowledge base for unstructured information such as
    company history, mission/values, culture, and floor descriptions.

    Args:
        query: The employee's natural language question.
    """
    return search_knowledge_base(query)
