"""
Thin retrieval layer over the vector store. Keeps tools/vector_tool.py
from having to know how the store was built or configured.
"""

from functools import lru_cache

from langchain_qdrant import QdrantVectorStore

from onboard_agent.vectorstore.creation import build_vector_store


# FIX (best practice): build the store lazily on first search instead of at import
# time. The old module-level `_vector_store = build_vector_store()` ran PDF loading,
# embedding calls (network + API key), and a Qdrant connection the instant anything
# imported this module — which broke `import`-only use, the test suite, and app
# startup. lru_cache keeps it a single shared instance, same as before, but on demand.
@lru_cache(maxsize=1)
def _get_vector_store() -> QdrantVectorStore:
    return build_vector_store()


def search_knowledge_base(query: str, k: int = 3) -> str:
    results = _get_vector_store().similarity_search(query, k=k)
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in results)
