"""
Thin retrieval layer over the vector store. Keeps tools/vector_tool.py
from having to know how the store was built or configured.
"""

from functools import lru_cache

from langchain_qdrant import QdrantVectorStore

from vectorstore.creation import build_vector_store


# Built lazily on first search (lru_cache) so importing this module never triggers
# PDF loading, embedding calls, or a Qdrant connection.
@lru_cache(maxsize=1)
def _get_vector_store() -> QdrantVectorStore:
    return build_vector_store()


def search_knowledge_base(query: str, k: int = 5) -> str:
    try:
        results = _get_vector_store().similarity_search(query, k=k)
    except Exception as exc:
        return f"The vector knowledge base is unavailable right now: {exc}"
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in results)
