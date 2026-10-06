# Vector-Brain

![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Vue 3](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs&logoColor=white)
![PostgreSQL 16 + pgvector](https://img.shields.io/badge/PostgreSQL_16-pgvector-336791?logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-gpt--oss--120b-F55036)

**An AI-powered multi-document research notebook that turns your PDFs into a searchable second brain.**

Upload PDFs, ask questions across all of them, and get streaming answers with
clickable citations to the exact passages — page numbers included.

**[🚀 Live Demo](https://itinerary-rehire-ramrod.ngrok-free.dev)**

*The demo is shared from a local instance via ngrok — it is reachable while
that instance is running.*

## Features

- **Multi-document Q&A** — ask one question across your entire library; answers
  synthesize evidence from every relevant document.
- **Trustworthy citations** — every claim carries a clickable `[n]` citation
  linked to its source passage (document, page, relevance score, excerpt).
- **Honest refusals** — when no retrieved passage supports an answer, the
  assistant declines plainly and shows **no** citations. Refusals are detected
  server-side, so the client can never display sources on a non-answer.
- **Document scoping** — restrict any question to a hand-picked subset of
  documents (`document_ids` filtering, enforced server-side).
- **Live ingestion pipeline** — uploads stream through Upload → Docling parse →
  Chunk → Embed → Index with real progress and per-stage status.
- **Library management** — grid/list views, search, sort, filter, favorites,
  duplicate detection (SHA-256 → `409`), live indexing status.
- **Streaming answers** — token-by-token SSE streaming from Groq, with sources
  delivered before the first token.
- **Polished UI** — Light / Dark / Midnight / High-Contrast themes, 6 accent
  colors, density and reduced-motion preferences, all persisted locally.
- **Mock modes** — run the entire app and test suite with no Groq key, no
  model download, and no network access.

## Architecture

```mermaid
flowchart LR
    PDF["PDF uploads"] --> DL["Docling<br/>page-aware parsing"]
    DL --> CH["Overlapping chunker<br/>1000 chars · 150 overlap"]
    CH --> EMB["all-MiniLM-L6-v2<br/>384-dim embeddings"]
    EMB --> PG[("PostgreSQL 16 + pgvector<br/>ivfflat cosine index")]
    Q["User question"] --> QE["Query embedding"]
    QE --> RET["Cosine similarity search<br/>top_k × 2 → threshold 0.30 → top_k"]
    PG --> RET
    RET --> CTX["Numbered context block<br/>[1] … [n]"]
    CTX --> GROQ["Groq · openai/gpt-oss-120b<br/>SSE streaming"]
    GROQ --> ANS["Answer with [n] citations"]
```

**Why each piece exists:**

| Component | Role |
|---|---|
| **Docling** | Converts PDFs to reading-order text with page provenance — citations need page numbers, so the parser must preserve them. |
| **Overlapping chunker** | 1000-char windows with 150-char overlap keep concepts from being split across chunk boundaries. |
| **all-MiniLM-L6-v2** | 384-dim embeddings: small, fast, CPU-friendly, and strong enough for semantic search over study notes. |
| **PostgreSQL + pgvector** | Documents and vectors live in one store, so deletes cascade and metadata stays consistent. `ivfflat … vector_cosine_ops` indexes ANN search. |
| **Cosine retrieval** | Over-fetch (`top_k × 2`), apply the similarity threshold, then trim to `top_k` — exact control over what reaches the LLM. |
| **Groq** | Low-latency inference (`openai/gpt-oss-120b`) with OpenAI-compatible streaming. |
| **SSE streaming** | Sources are emitted as an event *before* the first token, so the UI can render citations the moment text arrives. |
| **Vue 3 frontend** | Home dashboard, Library, and Notebook views with theming and local-only preferences. |

Full detail: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Screenshots

A dark-theme tour of the real application, captured from a live instance
with a 3-document demo library.

**Home Dashboard** — library stats, recent documents, and quick actions:

![Home Dashboard](docs/screenshots/01-home.png)

**Multi-document Library** — every PDF parsed, chunked, embedded, and Ready:

![Multi-document Library](docs/screenshots/02-library.png)

**Notebook — RAG with Citations** — streaming answers with clickable `[n]`
citations and a Sources panel (document, pages, relevance, excerpt):

![Notebook — RAG with Citations](docs/screenshots/03-notebook-chat.png)

**Multi-document Query** — scope a question to any subset of documents
("2 of 3 documents in scope") and get answers grounded across them:

![Multi-document Query](docs/screenshots/04-multi-doc.png)

**Upload** — drag-and-drop PDF ingestion with per-stage pipeline progress
(Docling → chunk → embed → index):

![Upload](docs/screenshots/05-upload.png)

**Chat History** — ChatGPT-style conversation sidebar with inline
rename/delete and full conversation restore:

![Chat History](docs/screenshots/06-history.png)

**Settings** — themes, accent colors, density, retrieval depth, and citation
display; everything stored locally:

![Settings](docs/screenshots/07-settings.png)

## 📚 Knowledge Bytes

Understand how Vector-Brain works internally through guided, code-specific
Knowledge Bytes generated from the actual implementation — each byte names
the real source files and functions, shows actual snippets, and explains
what the code does, why it exists, and how it connects to the rest of the
project.

Read them in order — start with `01_System_Architecture.md`:

**[Explore the Knowledge Bytes →](knowledge-bytes/)**

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS v4 |
| Backend | FastAPI, Pydantic v2, psycopg 3 (binary + pool) |
| PDF parsing | Docling |
| Embeddings | sentence-transformers · all-MiniLM-L6-v2 (384-dim) |
| Database | PostgreSQL 16 + pgvector (`vector(384)`, ivfflat cosine index) |
| LLM | Groq `openai/gpt-oss-120b` (OpenAI-compatible, SSE streaming) |
| Tests | pytest (backend), Vitest (frontend) |

## How It Works

1. **Upload** — `POST /api/documents` accepts a PDF (≤ 50 MB), dedupes by
   SHA-256, and returns `202` immediately.
2. **Ingest** — a background task parses the PDF with Docling (keeping page
   numbers), splits text into overlapping chunks, embeds each chunk with
   MiniLM, and stores vectors in pgvector. Status moves
   `processing → ready` (or `failed`, with the error — never a silent drop).
3. **Ask** — your question is embedded with the same model; pgvector returns
   the most similar chunks across all (or selected) documents.
4. **Answer** — chunks are formatted as a numbered context block and streamed
   to Groq, which answers *only* from the provided excerpts. `[n]` markers in
   the answer map to the source panel: document, page, relevance, excerpt.
5. **Decline** — if nothing passes the similarity threshold (or the model
   refuses), the response is a plain declined answer with zero sources.

## Installation

### Prerequisites

- **Python 3.12** (3.10–3.12 supported; 3.13 is *not* — pinned `torch`/`numpy`
  have no 3.13 wheels)
- **Node.js 18+**
- **Docker** (for PostgreSQL), or a local PostgreSQL 16 + pgvector install

### 1. Database

```bash
docker compose up -d db
```

This starts `pgvector/pgvector:pg16` with database/user/password `vectorbrain`
on port `5432`. The backend applies `backend/migrations/001_init.sql`
automatically on startup (enables `pgvector`, creates tables and the cosine
index). Prefer a local install? Run `./scripts/setup_db.sh` instead.

### 2. Backend

```bash
cd backend
cp ../.env.example .env   # set GROQ_API_KEY (optional) and DATABASE_URL
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

> First run downloads the embedding model (~90 MB). Without `GROQ_API_KEY`
> the API runs in clearly-labeled mock mode. On Apple Silicon, plain
> `pip install -r requirements.txt` is correct — no `--index-url` needed.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173 — /api is proxied to :8000
```

Open **http://localhost:5173**.

## Environment Variables

All settings come from the environment (see [`.env.example`](.env.example);
copy it to `backend/.env`):

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain` | — |
| `GROQ_API_KEY` | _(empty)_ | Empty → mock answer mode |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | — |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | — |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim |
| `MOCK_EMBEDDINGS` | `false` | `true` → deterministic offline test embeddings |
| `TOP_K` / `SCORE_THRESHOLD` | `6` / `0.30` | Retrieval tuning |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `150` | Ingestion tuning |
| `MAX_UPLOAD_MB` | `50` | Upload guard |
| `UPLOAD_DIR` | `./uploads` | Temp staging for ingestion |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173,…` | Comma-separated |

## Running Locally

```bash
# terminal 1 — database
docker compose up -d db

# terminal 2 — backend (from backend/)
.venv/bin/uvicorn app.main:app --reload --port 8000   # → http://localhost:8000/docs

# terminal 3 — frontend (from frontend/)
npm run dev                                            # → http://localhost:5173
```

Backend must be launched from `backend/` (its `.env` is resolved relative to
the working directory). The Vite dev server proxies `/api` to the backend;
override the target with `VB_BACKEND_URL` if your backend runs elsewhere.

## Demo Workflow

### Download Demo Documents

Three realistic study documents ship with the repo — click to view or download
directly from GitHub:

- [Introduction_to_Machine_Learning.pdf](demo-pdfs/Introduction_to_Machine_Learning.pdf) —
  learning paradigms, the modeling workflow, overfitting, bias–variance, gradient descent
- [Neural_Networks_and_Deep_Learning.pdf](demo-pdfs/Neural_Networks_and_Deep_Learning.pdf) —
  perceptrons, activations, backpropagation, training with gradient descent, CNNs
- [Machine_Learning_Evaluation.pdf](demo-pdfs/Machine_Learning_Evaluation.pdf) —
  confusion matrix, precision/recall, F1, ROC-AUC, cross-validation, learning curves

### Quick Demo (5 minutes)

1. **Start Vector-Brain** (see [Running Locally](#running-locally)).
2. **Upload** the three PDFs from `demo-pdfs/` via *Add Documents* — watch the
   staged pipeline (Uploading → Parsing → Chunking → Embedding → Indexing).
3. **Open the Notebook** and ask a cross-document question (below).
4. **Click a `[n]` citation** — the Sources panel shows the exact passage:
   document, page, relevance bar, excerpt.
5. **Scope the search** — uncheck a document in *Search across* and ask again;
   retrieval is restricted server-side.
6. **Ask something the PDFs don't cover** — the assistant declines, with no
   citations shown.

Full scripted walkthrough: [`docs/DEMO.md`](docs/DEMO.md).

### Sample Questions

All answerable from the demo documents:

- *"What is the difference between precision and recall?"*
- *"How does backpropagation relate to gradient descent?"*
- *"Which concepts are shared between the machine learning and neural network documents?"*
- *"Explain overfitting and how it can be detected."*
- *"Compare the evaluation metrics discussed across the documents."*

## API Overview

Base URL (dev): `http://localhost:8000` · interactive docs at `/docs`.

| Method & Path | Description |
|---|---|
| `POST /api/documents` | Upload a PDF → `202`, ingestion runs in the background |
| `GET /api/documents` | List documents with status (`processing`/`ready`/`failed`) |
| `DELETE /api/documents/{id}` | Delete a document and all its chunks (cascade) |
| `POST /api/chat` | Streaming SSE answer: `sources` event → `token` events → `done` |
| `POST /api/chat/sync` | Non-streaming JSON answer (tests, simple clients) |
| `GET /api/health` | Service + dependency status (`groq_mode`, counts) |

`POST /api/chat` accepts `question`, optional `top_k` (1–20), and optional
`document_ids` to scope retrieval. Full reference: [`docs/API.md`](docs/API.md).

## Project Structure

```
vector-brain/
├── backend/
│   ├── app/                    # FastAPI: api/, config, db, ingest, embeddings,
│   │                           # retrieval, llm, pipeline
│   ├── migrations/001_init.sql # PostgreSQL + pgvector schema
│   ├── tests/                  # pytest: unit (mocked) + DB integration
│   └── requirements.txt
├── frontend/                   # Vue 3 + Vite: Home, Library, Notebook,
│                               # Favorites, Recent, Settings, Profile, theming
│   └── src/
├── demo-pdfs/                  # 3 realistic study PDFs for first-run demos
├── knowledge-bytes/            # guided tour of the actual codebase (docs only)
├── docs/                       # architecture, API, demo script, evaluation
├── scripts/setup_db.sh         # local PostgreSQL setup (no Docker)
├── docker-compose.yml          # pgvector/pgvector:pg16, one command
├── .env.example
└── README.md
```

## Knowledge Bytes

[`knowledge-bytes/`](knowledge-bytes/) is a guided tour of the actual
Vector-Brain implementation — numbered bytes (`01`–`08`) you read in order,
each mapping to real source files with real snippets. The methodology that
defines how a Knowledge Byte is written lives in
[`knowledge-bytes/knowledge-bytes-prompt.md`](knowledge-bytes/knowledge-bytes-prompt.md)
(model-agnostic, reusable for any codebase — not a Vector-Brain feature).

## Testing

```bash
cd backend
.venv/bin/python -m pytest tests/ -q        # unit suite (offline, mocked)

# real pgvector round-trip (needs PostgreSQL):
VECTORBRAIN_TEST_DATABASE_URL=postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain_test \
  .venv/bin/python -m pytest tests/test_db_integration.py -v

cd ../frontend
npm test                                     # frontend unit tests
npm run build                                # production build
```

## Limitations

- **Single-user, local-first** — no authentication or per-user document
  ownership; designed to run on your own machine.
- **PDF-only ingestion** — other formats (EPUB, Markdown, web pages) are not
  parsed yet.
- **English-optimized embeddings** — all-MiniLM-L6-v2 is strongest on English
  text; other languages retrieve less reliably.
- **PostgreSQL required** — there is no embedded-database fallback; the app
  fail-fasts at boot if the database is unreachable.
- **Groq key needed for live answers** — without one, answers run in
  clearly-labeled mock mode.
- **Python ≤ 3.12** — pinned `torch`/`numpy` versions have no Python 3.13 wheels.

## Future Improvements

- Multi-user support with authentication and per-user document scoping
- Additional ingestion formats (EPUB, Markdown, HTML)
- Hybrid search (BM25 + vector) and HNSW indexing for larger corpora
- Real task queue (Celery/RQ) for multi-worker ingestion
- Conversation memory across sessions
- RAG evaluation harness (retrieval precision, citation faithfulness)

## Docs

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — pipeline, modules, design decisions, failure modes
- [`docs/API.md`](docs/API.md) — endpoint reference with SSE event shapes
- [`docs/DEMO.md`](docs/DEMO.md) — 5-minute scripted demo + public-demo (ngrok) guide
- [`docs/EVALUATION.md`](docs/EVALUATION.md) — how to verify retrieval and answer quality

## Security Notes

- Secrets live only in `backend/.env` (git-ignored); `.env.example` ships with blanks.
- Uploads are validated (PDF type, size cap, non-empty) and temp files are
  always cleaned up after ingestion.
- All SQL is parameterized; no string-built queries.
- CORS is restricted to the configured frontend origins.
