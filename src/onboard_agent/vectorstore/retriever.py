"""
Thin retrieval layer over the vector store. Keeps tools/vector_tool.py
from having to know how the store was built or configured.
"""

from onboard_agent.vectorstore.creation import build_vector_store

# Built once at import time. For a larger app this would likely be lazy
# or dependency-injected instead of a module-level singleton.
_vector_store = build_vector_store()


def search_knowledge_base(query: str, k: int = 3) -> str:
    results = _vector_store.similarity_search(query, k=k)
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in results)
