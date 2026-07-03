import json
import os
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
#from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma  # maintained package
# remove OpenAIEmbeddings import
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load environment variables from .env in project root
load_dotenv()

CHUNKS_PATH = Path("data/processed/chunks.jsonl")
VECTORSTORE_DIR = "vectorstore"
COLLECTION_NAME = "policy_chunks"


def _load_chunks() -> List[Dict[str, Any]]:
    """Load JSONL chunks produced by ingestion."""
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"{CHUNKS_PATH} not found. Run ingestion first.")
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _get_required_env(name: str) -> str:
    """Return required environment variable or raise clear error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Local/free embedding model to avoid API quota limits.
    all-MiniLM-L6-v2 is lightweight and good enough for assignment scope.
    """
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
    return HuggingFaceEmbeddings(model_name=model_name)

def build_vectorstore() -> Chroma:
    """Build persistent Chroma index from chunks."""
    chunks = _load_chunks()
    if not chunks:
        raise ValueError("No chunks available to index.")

    texts = [c["text"] for c in chunks]
    metadatas = [{
        "chunk_id": c["chunk_id"],
        "doc_id": c["doc_id"],
        "doc_title": c["doc_title"],
        "source_path": c["source_path"],
        "chunk_index": c["chunk_index"],
    } for c in chunks]
    ids = [c["chunk_id"] for c in chunks]

    embedding = _get_embedding_model()

    vs = Chroma.from_texts(
        texts=texts,
        embedding=embedding,
        metadatas=metadatas,
        ids=ids,
        persist_directory=VECTORSTORE_DIR,
        collection_name=COLLECTION_NAME,
    )
    return vs


def load_vectorstore() -> Chroma:
    """Load existing persistent vectorstore."""
    embedding = _get_embedding_model()
    return Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embedding,
        collection_name=COLLECTION_NAME,
    )


def retrieve(question: str, k: int = 4):
    """Retrieve top-k similar chunks for question."""
    vs = load_vectorstore()
    return vs.similarity_search(question, k=k)


if __name__ == "__main__":
    build_vectorstore()
    print("Vectorstore built successfully.")