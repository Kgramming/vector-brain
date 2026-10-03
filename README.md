# Vector-Brain — Notebook LLM Lite 🧠

A **"second brain" for studying**: upload multiple PDFs, ask questions across
all of them, and get streaming answers with **citations** to the exact passages.
Plus **Knowledge Bytes** — architecture-first, 10-second explainers for code and
technical content.

```
PDFs → Docling → chunks → 384-dim embeddings → PostgreSQL + pgvector
     → cosine search → Groq → answer + citations → Vue.js
```

## Features

- **Multi-PDF library** — drag-drop upload, Docling parsing with page provenance,
  background ingestion with live status, sha256 dedupe, delete cascades to chunks
- **Semantic search Q&A** — 384-dim embeddings (all-MiniLM-L6-v2), pgvector cosine
  search across *all* documents, similarity threshold, streaming answers
- **Trustworthy citations** — numbered sources with excerpts, page numbers and
  similarity scores; refusals (`[DECLINED]`) are detected server-side and carry
  **no** citations
- **Knowledge Bytes** — paste code → streaming BYTE N explainers
  (ROLE / FLOW / CONNECTS TO / WHY / KEY CODE → PUTTING IT TOGETHER)
- **Mock modes** — run the full app and test suite with no Groq key, no model
  download, no network
- **Tested** — backend pytest suite (unit + real-DB integration), frontend unit tests

## Quickstart

### 1. Database (PostgreSQL 16 + pgvector)

Easiest — Docker:

```bash
docker compose up -d db
```

Or a local install, then:

```bash
./scripts/setup_db.sh
```

### 2. Backend

```bash
cd backend
cp ../.env.example .env        # then set GROQ_API_KEY (optional) and DATABASE_URL
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> First run downloads the embedding model (~90 MB) and applies DB migrations
> automatically. Without `GROQ_API_KEY` the API runs in clearly-labeled mock mode.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api → :8000)
```

## Configuration

All settings via environment (see [`.env.example`](.env.example)):

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain` | — |
| `GROQ_API_KEY` | _(empty)_ | Empty → mock answer mode |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | — |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim |
| `MOCK_EMBEDDINGS` | `false` | `true` → deterministic test embeddings |
| `TOP_K` / `SCORE_THRESHOLD` | `6` / `0.30` | Retrieval tuning |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` | Ingestion tuning |
| `MAX_UPLOAD_MB` | `50` | Upload guard |

## Testing

```bash
cd backend
.venv/bin/python -m pytest tests/ -q                      # unit suite (offline)
VECTORBRAIN_TEST_DATABASE_URL=postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain_test \
  .venv/bin/python -m pytest tests/test_db_integration.py -v   # real pgvector round-trip

cd ../frontend && npm test                                 # frontend unit tests
```

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — pipeline, modules, design decisions, failure modes
- [`docs/API.md`](docs/API.md) — endpoint reference with SSE event shapes
- [`docs/DEMO.md`](docs/DEMO.md) — 5-minute scripted demo
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — how to verify retrieval/answer quality
- Interactive API docs at `http://localhost:8000/docs` when the backend runs

## Project structure

```
vector-brain/
├── backend/
│   ├── app/                # FastAPI app: api/, config, db, ingest, embeddings,
│   │                       # retrieval, llm, knowledge_bytes, pipeline
│   ├── migrations/001_init.sql   # PostgreSQL + pgvector schema
│   ├── tests/              # pytest: unit (mocked) + DB integration
│   └── requirements.txt
├── frontend/               # Vue 3 + Vite + Tailwind: Library, Notebook, Knowledge Bytes
├── docs/                   # architecture, API, demo, evaluation
├── scripts/setup_db.sh
├── docker-compose.yml      # postgres:16 + pgvector, one command
└── .env.example
```

## Security notes

- Secrets live only in `.env` (git-ignored); `.env.example` ships with blanks.
- Uploads are validated (PDF magic via extension + content-type, size cap, empty
  check) and temp files are always cleaned up after ingestion.
- SQL is parameterized throughout; no string-built queries.
- CORS is restricted to the configured frontend origins.
