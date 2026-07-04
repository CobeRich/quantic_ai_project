# AI Tooling Usage

## Tools Used
- ChatGPT / AI assistant for:
  - project scaffolding and task planning
  - debugging environment/API errors
  - drafting initial implementations for ingestion, retrieval, and evaluation
  - improving documentation and submission-readiness
- GitHub Copilot (optional, if used in your IDE) for inline code suggestions and refactors.

## What Worked Well
- Rapidly generated baseline modules (`ingest.py`, `rag.py`, `web.py`, `eval.py`)
- Faster troubleshooting for provider/API configuration errors
- Helped structure project to align with rubric requirements
- Accelerated documentation drafting for final submission

## What Needed Manual Engineering
- Environment and API key/quota debugging
- Provider switching and compatibility checks
- Data refresh pipeline (re-ingest/re-index flow)
- Metric interpretation and final quality validation
- End-to-end testing and endpoint behavior verification

## Quality Control Process
- Manually reviewed generated code before committing
- Ran local tests and endpoint checks
- Rebuilt index after corpus changes
- Executed evaluation and validated output artifacts (`results.csv`)
- Performed manual spot checks of answer grounding and citation relevance
