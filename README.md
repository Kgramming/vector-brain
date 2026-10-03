# Vector-Brain — Notebook LLM Lite 🧠

A **"second brain" for studying**: upload multiple PDFs, ask questions across
all of them, and get streaming answers with **citations** to the exact passages.

```
PDFs → Docling → chunks → 384-dim embeddings → PostgreSQL + pgvector
     → cosine search → Groq → answer + citations → Vue.js
```

## Features

- **Home dashboard** — stats (documents, pages, chunks), recent documents and
  questions, onboarding empty state
- **Library** — grid/list views, search, sort, filter, favorites, document cards
  with live indexing status; drag-drop upload with an animated
  Upload → Docling → Chunk → Embed → Index pipeline
- **Notebook** — document scope selector, markdown answers, clickable **[1]**
  citations, collapsible source panel (page, relevance, excerpt), example
  prompts, conversation history, `⌘/Ctrl+↵` to send
- **Semantic search Q&A** — 384-dim embeddings (all-MiniLM-L6-v2), pgvector cosine
  search across *all* documents (or a selected subset via `document_ids`),
  similarity threshold, streaming answers
- **Trustworthy citations** — numbered sources with excerpts, page numbers and
  similarity scores; refusals (`[DECLINED]`) are detected server-side and carry
  **no** citations
- **Themes** — Light, Dark, Midnight, High Contrast + 6 accent colors, density
  and motion preferences, all persisted locally
- **Knowledge Bytes** — architecture-first, 10-second code explainers, available
  as a quiet action inside the Notebook (not a primary destination)
- **Mock modes** — run the full app and test suite with no Groq key, no model
  download, no network
- **Tested** — backend pytest suite (unit + real-DB integration), frontend unit tests

## Demo PDFs

`demo-pdfs/` ships three realistic study documents for a first-run demo:

| File | Covers |
|---|---|
| `Introduction_to_Machine_Learning.pdf` (8 pp.) | supervised learning, regression, classification, overfitting, evaluation |
| `Neural_Networks_and_Deep_Learning.pdf` (9 pp.) | neurons, activations, backpropagation, optimization, CNNs |
| `Machine_Learning_Evaluation.pdf` (9 pp.) | precision/recall, F1, ROC-AUC, confusion matrix |

Upload all three, then try: *"How does backpropagation relate to gradient
descent?"* or *"Compare precision and recall — when does each matter?"*
Answers cite across documents. See [`docs/DEMO.md`](docs/DEMO.md) for the
full 5-minute script.

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

### Heavy dependencies (Docling)

`requirements.txt` includes Docling (PDF parsing) and sentence-transformers,
which pull in PyTorch. On a CPU-only machine, install the CPU wheel **first**
to avoid the multi-GB CUDA build:

```bash
pip install "torch==2.5.1" --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Docling also downloads its layout/OCR models (~1 GB) into `~/.cache/docling`
on first PDF parse — this happens inside the background ingestion task, so
the first upload takes longer. The unit test suite never needs these:
it runs fully offline with `MOCK_EMBEDDINGS=true`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api → :8000)
```

### Ports & connecting the two

Defaults: frontend `:5173` → backend `:8000` via the Vite dev proxy
(`VB_BACKEND_URL` overrides the proxy target). CORS allows
`:5173`/`:5174` on both `localhost` and `127.0.0.1`
(override with `CORS_ORIGINS` in `backend/.env`).

If your backend runs on a different port, e.g. `:8001`:

```bash
# option A — dev proxy (recommended):
VB_BACKEND_URL=http://127.0.0.1:8001 npm run dev

# option B — browser talks to the backend directly (needs CORS, already
# includes :5173/:5174; no proxy involved):
# frontend/.env:  VITE_API_URL=http://127.0.0.1:8001
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
├── frontend/               # Vue 3 + Vite: app shell, Home, Library, Notebook,
│                           # Favorites, Recent, Settings, Profile, theming
├── demo-pdfs/              # 3 realistic study PDFs for first-run demos
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
