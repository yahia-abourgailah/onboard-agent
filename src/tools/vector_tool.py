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
    if not query or not query.strip():
        return "No question was provided to search for."

    try:
        results = search_knowledge_base(query)
    except Exception as e:
        return (
            f"Error: the knowledge base search failed ({e}). "
            "Try rephrasing the question or check with HR."
        )

    if not results:
        return "No relevant information was found in the knowledge base for that question."

    return results
