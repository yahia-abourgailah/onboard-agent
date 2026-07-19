from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def load_onboarding_docs(data_dir: Path = DATA_DIR) -> list[Document]:
    """Load every PDF in the data directory into raw page-level Documents."""
    pdf_paths = sorted(data_dir.glob("*.pdf"))

    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {data_dir}")

    documents: list[Document] = []
    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()

        for page in pages:
            page.metadata["topic"] = pdf_path.stem
            page.metadata["source"] = pdf_path.name

        documents.extend(pages)

    return documents


def chunk_documents(
    documents: list[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Split page-level Documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def build_vector_store(
    collection_name: str = "onboarding_kb",
    data_dir: Path = DATA_DIR,
    qdrant_url: str | None = None,
) -> QdrantVectorStore:
    # Config-via-env (see config.py): default to the configured Qdrant URL rather
    # than hardcoding localhost, so each environment points at its own instance.
    qdrant_url = qdrant_url or Settings().QDRANT_URL
    documents = load_onboarding_docs(data_dir)
    chunks = chunk_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    return QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=qdrant_url,
        collection_name=collection_name,
    )
