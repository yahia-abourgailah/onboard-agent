"""
Thin retrieval layer over the vector store. Keeps tools/vector_tool.py
from having to know how the store was built or configured.
"""

from vectorstore.creation import get_vector_store


def search_knowledge_base(query: str, k: int = 8) -> str:
    try:
        results = get_vector_store().similarity_search(query, k=k)
    except Exception as exc:
        return f"The vector knowledge base is unavailable right now: {exc}"
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in results)
