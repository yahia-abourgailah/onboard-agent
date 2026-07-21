from langchain_core.tools import tool

from vectorstore.retriever import search_knowledge_base


@tool
def query_vector_db(query: str) -> str:
    """
    Search the company knowledge base for unstructured information such as
    company history, mission/values, culture, policies, hiring documents and floor descriptions.

    Args:
        query: The employee's natural language question.
    """
    return search_knowledge_base(query)
