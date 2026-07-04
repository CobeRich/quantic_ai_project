# Design and Evaluation

## 1) Design and Architecture Decisions

## Problem
Build a RAG-based policy assistant that answers user questions using a corpus of company policy/procedure documents, with citations and basic guardrails.

## High-Level Architecture
1. **Ingestion (`app/ingest.py`)**
   - Parses PDF/HTML/MD/TXT files from `data/raw/`
   - Cleans text and applies deterministic chunking
   - Writes chunk records to `data/processed/chunks.jsonl`

2. **Indexing (`app/rag.py`)**
   - Embeds chunks using `sentence-transformers/all-MiniLM-L6-v2`
   - Stores vectors + metadata in local persistent **Chroma** (`vectorstore/`)

3. **Retrieval + Generation (`app/rag.py`)**
   - Top-k similarity retrieval (`k=4`)
   - Prompts LLM with retrieved context and citation instructions
   - Returns answer + citations + snippets

4. **Guardrails (`app/guardrails.py`)**
   - Refuse clearly out-of-corpus questions
   - Limit answer length
   - Always return citations/snippets for traceability

5. **Web App (`app/web.py`)**
   - `GET /` chat UI
   - `POST /chat` API for question answering
   - `GET /health` status endpoint

## Technology Choices and Why
- **Flask**: lightweight and quick for required endpoints
- **Chroma (local)**: easy local persistence, no external DB ops required
- **HuggingFace local embeddings**: avoids paid embedding API dependence
- **Groq-hosted LLM**: fast generation via OpenAI-compatible API
- **LangChain components**: speeds integration of retrieval/generation flow

## Chunking / Retrieval Choices
- Character-window chunking with overlap for context continuity
- Deterministic chunking to improve reproducibility
- Top-k retrieval with metadata for citation and snippet rendering

---

## 2) Evaluation Approach

## Evaluation Dataset
- `data/eval/questions.csv`
- 30 questions spanning:
  - PTO
  - security
  - expense
  - remote work
  - holidays
  - compliance/procedures

## Metrics
### Required
1. **Groundedness (proxy):** answer produced with retrieved supporting snippets
2. **Citation Accuracy (proxy):** citation list is present and mapped to retrieved chunks
3. **Latency (required):** p50 and p95 request latency

### Optional
4. **Exact Match**
5. **Partial Match**

## Method
- Run `python -m app.eval`
- For each question:
  - call RAG endpoint logic
  - capture latency
  - compute heuristic metrics
  - write row-level results to `data/eval/results.csv`

---

## 3) Results Summary

From latest run:

- Questions: **30**
- Groundedness (heuristic): **100.00%**
- Citation Accuracy proxy (citation present): **100.00%**
- Exact Match (optional): **0.00%**
- Partial Match (optional): **0.00%**
- Latency p50: **7575.27 ms**
- Latency p95: **8796.10 ms**

---

## 4) Interpretation

- High groundedness/citation proxy indicates the system consistently returns retrieved evidence and citations.
- EM/PM = 0% is expected under strict lexical matching when model wording differs from short gold answers.
- Latency (~7.6s p50, ~8.8s p95) is acceptable for a demo prototype but can be improved.

---

## 5) Limitations and Future Improvements

1. Add a reranker to improve retrieval precision.
2. Replace heuristic groundedness/citation checks with human-verified labels for full reliability.
3. Optimize latency via:
   - shorter prompt context
   - caching repeated queries
   - faster/smaller generation model for some queries
4. Add ablation experiments:
   - compare chunk sizes
   - compare top-k values
   - compare prompt variants
5. Expand guardrails with stricter policy-topic classifier and answer formatting constraints.
