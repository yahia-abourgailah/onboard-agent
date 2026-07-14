"""
Creates and seeds the Chroma vector store with onboarding knowledge-base
documents (company history, values, floor descriptions, etc.).

Import get_vector_store() from here wherever the store is needed
(currently just tools/vector_tool.py, via retriever.py).
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

ONBOARDING_DOCS = [
    Document(
        page_content="The company was founded in 2015 by two engineers who wanted "
        "to make internal tools less painful. We grew from 2 to 300 people by 2024.",
        metadata={"topic": "history"},
    ),
    Document(
        page_content="Our core values are curiosity, ownership, and respect. "
        "We favor written communication and default to transparency.",
        metadata={"topic": "values"},
    ),
    Document(
        page_content="Floor 1 has reception, the cafeteria, and guest meeting rooms.",
        metadata={"topic": "floor_1"},
    ),
    Document(
        page_content="Floor 2 houses the Design and Marketing teams, plus a quiet "
        "focus room and a small library.",
        metadata={"topic": "floor_2"},
    ),
    Document(
        page_content="Floor 3 houses the Engineering and Product teams, along with "
        "the server room and the main all-hands space.",
        metadata={"topic": "floor_3"},
    ),
]


def build_vector_store(collection_name: str = "onboarding_kb") -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma.from_documents(
        documents=ONBOARDING_DOCS,
        embedding=embeddings,
        collection_name=collection_name,
    )
