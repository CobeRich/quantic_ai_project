import os
import re
import json
from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader
from bs4 import BeautifulSoup
import markdown as md

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"

def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n".join(pages)

def read_html(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

def read_md(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    html = md.markdown(raw)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def load_doc(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return read_pdf(path)
    if ext in [".html", ".htm"]:
        return read_html(path)
    if ext == ".md":
        return read_md(path)
    if ext == ".txt":
        return read_txt(path)
    return ""

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    # deterministic chunking
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap
    return chunks

def ingest():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    docs = sorted([p for p in RAW_DIR.glob("*") if p.is_file()])

    total_chunks = 0
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for doc_path in docs:
            raw_text = load_doc(doc_path)
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue

            chunks = chunk_text(cleaned, chunk_size=900, overlap=150)
            for i, chunk in enumerate(chunks):
                record: Dict = {
                    "chunk_id": f"{doc_path.stem}::chunk_{i}",
                    "doc_id": doc_path.stem,
                    "doc_title": doc_path.name,
                    "source_path": str(doc_path),
                    "chunk_index": i,
                    "text": chunk,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_chunks += 1

    print(f"Ingestion complete. Wrote {total_chunks} chunks to {CHUNKS_PATH}")

if __name__ == "__main__":
    ingest()
