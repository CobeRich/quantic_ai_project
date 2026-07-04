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
from langchain_openai import ChatOpenAI

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


def _get_llm() -> ChatOpenAI:
    """
    OpenAI-compatible chat model client.
    You can point this to OpenAI/OpenRouter/Groq compatible endpoints.
    """
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    max_tokens = int(os.getenv("MAX_ANSWER_TOKENS", "300"))

    if not api_key:
        raise ValueError("Missing LLM_API_KEY for generation.")

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0,
        max_tokens=max_tokens,
    )


def build_vectorstore() -> Chroma:
    """Build persistent Chroma index from chunks."""
    chunks = _load_chunks()
    if not chunks:
        raise ValueError("No chunks available to index.")

    #texts = [c["text"] for c in chunks]
    texts = []
    for c in chunks:
        doc_title = c.get("doc_title", "unknown")
        chunk_text = c.get("text", "")
        # section_hint optional; use chunk index if you don't have headings
        section_hint = str(c.get("chunk_index", "unknown"))
        text_for_embedding = f"Document: {doc_title}\nSection: {section_hint}\n\n{chunk_text}"
        texts.append(text_for_embedding)

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


def retrieve_with_scores(question: str, k: int = 6, min_score: float = 0.35):
    vs = load_vectorstore()
    # Lower distance = better match for Chroma
    pairs = vs.similarity_search_with_score(question, k=k)
    filtered = []
    for doc, score in pairs:
        if score <= min_score:
            filtered.append((doc, score))
    # Fallback: if threshold too strict, keep top 2
    if not filtered:
        filtered = pairs[:2]
    return filtered


def answer_with_rag(question: str, k: int = 4) -> Dict[str, Any]:
    """
    End-to-end RAG answer:
    1) retrieve chunks
    2) prompt model with strict grounding/citation rules
    3) return answer + citations + snippets
    """
    doc_pairs = retrieve_with_scores(question, k=k, min_score=float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.35")))
    #docs = [d for d, _ in doc_pairs]
#    docs = retrieve(question, k=k)

    if not doc_pairs:
        return {
            "answer": "I can only answer based on the policy corpus, and I found no relevant content.",
            "citations": [],
            "snippets": [],
        }

    context_blocks = []
    citations = []
    snippets = []

    for d, score in doc_pairs:
        meta = d.metadata or {}
        chunk_text = d.page_content.strip()
        doc_title = meta.get("doc_title", "unknown")
        chunk_id = meta.get("chunk_id", "unknown")
        source_path = meta.get("source_path", "")

        # Build context block with stable citation identifiers
        context_blocks.append(
            f"[{chunk_id}] ({doc_title})\n{chunk_text}"
        )

        citations.append({
            "chunk_id": chunk_id,
            "doc_title": doc_title,
            "source_path": source_path,
        })

        # Short snippet preview for UI/API response
        snippets.append({
            "chunk_id": chunk_id,
            "doc_title": doc_title,
            "score": float(score),
            "snippet": chunk_text[:280] + ("..." if len(chunk_text) > 280 else ""),
        })

    context = "\n\n".join(context_blocks)

    system_prompt = (
        "You are a company policy assistant. "
        "Answer ONLY using the provided context. "
        "If the answer is not in context, say you don't have enough policy evidence. "
        "Always include supporting citation chunk IDs in your prose like [doc::chunk_x]. "
        "Keep answers concise."
    )

    user_prompt = f"""Question: {question}

Context:
{context}

Return:
1) concise answer grounded only in context
2) include citation chunk IDs inline
"""
    try:
        llm = _get_llm()
        resp = llm.invoke([
        ("system", system_prompt),
        ("user", user_prompt),
        ])
        answer_text = resp.content

        return {
            "answer": resp.content,
            "citations": citations,
            "snippets": snippets,
        }
    except Exception as e:
        # Fallback mode: if remote LLM fails (quota/rate-limit/auth),
        # return an extractive answer from top snippets so /chat never 500s.
        top = snippets[:2]
        joined = " ".join([s["snippet"] for s in top]).strip()
        answer_text = (
            "LLM generation is temporarily unavailable (provider quota/rate-limit). "
            "Based on retrieved policy text: " + joined
        )

    return {
        "answer": answer_text,
        "citations": [],
        "snippets": [],
    }


if __name__ == "__main__":
    build_vectorstore()
    print("Vectorstore built successfully.")