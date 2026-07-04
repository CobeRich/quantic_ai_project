# quantic_ai_project
# Quantic AI Project: Policy RAG Assistant

A Retrieval-Augmented Generation (RAG) web application that answers questions about a company policy corpus (PTO, security, expense, remote work, holidays, etc.) using document retrieval + LLM generation with citations.

## Features

- Multi-format policy ingestion: **PDF, HTML, Markdown, TXT**
- Deterministic chunking and metadata tracking
- Local vector index with **Chroma**
- Retrieval + generation pipeline with citations/snippets
- Guardrails:
  - Refuses out-of-scope questions
  - Limits answer length
  - Returns source citations/snippets
- Web app endpoints:
  - `GET /` simple chat UI
  - `POST /chat` API chat endpoint
  - `GET /health` health check
- Evaluation script for:
  - Groundedness (proxy)
  - Citation accuracy (proxy)
  - Optional exact/partial match
  - Latency p50/p95
- CI via GitHub Actions

---

## Repository Structure

```text
app/
  __init__.py
  web.py
  rag.py
  ingest.py
  eval.py
  guardrails.py
data/
  raw/
  processed/
  eval/
tests/
.github/workflows/ci.yml
requirements.txt
.env.example
README.md
design-and-evaluation.md
ai-tooling.md
```

---

## Setup

## 1) Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # mac/linux
# .venv\Scripts\activate       # windows
```

## 2) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Configure environment variables

Create `.env` in repo root (do not commit):

```env
LLM_API_KEY=your_provider_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TOP_K=4
MAX_ANSWER_TOKENS=300
```

---

## Data Ingestion and Indexing

Place policy files in `data/raw/` (5–20 files, ~30–120 pages total).

Then run:

```bash
python app/ingest.py
rm -rf vectorstore
python app/rag.py
```

If you update files in `data/raw/`, repeat the same 3 commands.

---

## Run the App

```bash
python run.py
```

Open:

- UI: `http://localhost:8000/`
- Health: `http://localhost:8000/health`

Example `/chat` request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the PTO carryover policy?"}'
```

---

## Testing

```bash
pytest -q
```

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push/PR:

- installs dependencies
- performs import/build check
- runs tests

---

## Evaluation

Create/edit `data/eval/questions.csv` with 15–30 questions:

```csv
id,question,gold_answer
1,How many PTO days are granted annually?,...
...
```

Run:

```bash
python -m app.eval
```

Outputs:

- `data/eval/results.csv`
- console summary (groundedness, citation accuracy proxy, EM/PM optional, p50/p95 latency)

---

## Notes

- This project uses local embeddings to reduce API cost.
- LLM generation uses an OpenAI-compatible endpoint (Groq in this setup).
A
A
A
- If provider quota/rate-limits occur, fallback behavior can still return retrieval-based evidence text.
