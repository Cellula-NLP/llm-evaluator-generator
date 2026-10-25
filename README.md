# LLM Evaluator-Generator Platform

Self-evaluating QA over external knowledge with an LCEL-orchestrated Generator ↔ Evaluator loop.

## Quickstart

```bash
cp .env.example .env      # add OPENAI_API_KEY
docker compose up --build
# → http://localhost:8000/ui/ingest