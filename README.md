# LLM Evaluator-Generator Platform

A self-evaluating question-answering platform built with **FastAPI, LangChain, and LCEL**. It uses a Generator–Evaluator feedback loop to create answers grounded in your uploaded knowledge.

<!-- Replace these paths with your actual frontend screenshots. -->
<p align="center">
  <img src="docs/screenshots/ingestion.png" alt="Knowledge ingestion interface" width="32%" />
  <img src="docs/screenshots/chat.png" alt="Question answering interface" width="32%" />
  <img src="docs/screenshots/loop-inspector.png" alt="Evaluation loop inspector" width="32%" />
</p>

## Features

- **Knowledge ingestion:** PDF, DOCX, TXT, PPTX, source code, web URLs, Wikipedia, and WAV audio.
- **RAG:** Chunks and indexes external knowledge in Qdrant for semantic retrieval.
- **Generator:** Answers using retrieved context and refuses when relevant context is unavailable.
- **Evaluator:** Reviews accuracy, relevance, completeness, and grounding; sends feedback when an answer needs improvement.
- **Bounded feedback loop:** Up to 4 iterations. If no answer is accepted, the latest answer is returned with a `Not Validated` warning.
- **Separate memories:** Generator and Evaluator keep independent, session-specific memories.
- **Redis caching:** Caches embeddings and retrieval results, with invalidation when knowledge sources change.

## Architecture

See the [workflow diagram](docs/workflow.mmd) for the system flow.

## Tech Stack

| Area | Technology |
|---|---|
| Backend | FastAPI, Uvicorn |
| LLMs | Groq (Llama 3.3 70B / GPT-OSS) |
| Orchestration | LangChain, LCEL |
| Vector database | Qdrant |
| Cache | Redis |
| Frontend | Jinja2, HTMX |
| Audio transcription | faster-whisper |
| Deployment | Docker Compose |

## Quickstart

### Requirements

- Python 3.10+
- Docker Desktop
- Git
- A Groq API key

### 1. Clone the repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Add your Groq API key and model settings to `.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GENERATOR_MODEL=openai/gpt-oss-120b
EVALUATOR_MODEL=openai/gpt-oss-20b
```

Do not commit your `.env` file or expose your API key.

### 3. Start Redis and Qdrant

```bash
docker compose up -d redis qdrant
```

### 4. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 5. Run the app

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/ui/ingest**.

## Using the Platform

1. Upload supported files or add a web/Wikipedia URL.
2. Ask questions about the indexed knowledge.
3. Use the **Loop Inspector** to review scores, feedback, and iterations.
4. Check whether the final answer was accepted or returned as `Not Validated`.

## Design Notes

- **Grounding:** If retrieval finds no relevant context, the system returns a refusal without calling the LLM.
- **Evaluation:** The Evaluator checks the generated answer and provides actionable feedback for another attempt.
- **Memory isolation:** `GeneratorMemory` and `EvaluatorMemory` are separate and namespaced by `session_id`.
- **Caching:** Redis reduces repeated embedding and retrieval work. Cached data is invalidated when its knowledge source changes.
- **Execution limit:** The feedback loop stops after 4 iterations to control latency and API usage.

> Evaluation helps improve answer quality, but it does not guarantee factual correctness.

## Notes

For Intel-based Macs, the project pins `numpy<2` and `torch==2.2.2` in `pyproject.toml` for compatibility.
