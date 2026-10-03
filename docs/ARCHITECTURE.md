# Vector-Brain — Architecture

> "Notebook LLM Lite": a second brain for studying. Upload multiple PDFs, ask
> questions across all of them, get answers with citations.

## Pipeline

```
PDFs
 ↓  (upload, sha256 dedupe, 50 MB limit)
Docling (DocumentConverter → reading-order text + page provenance)
 ↓
Overlapping chunker (1000 chars, 150 overlap, page_start/page_end kept)
 ↓
all-MiniLM-L6-v2 → 384-dim L2-normalized embeddings
 ↓
PostgreSQL + pgvector  (chunks.embedding vector(384), ivfflat cosine index)
 ↓
Cosine similarity search across ALL documents (top_k × 2 → threshold 0.30 → top_k)
 ↓
Numbered context block [1..n] + question → Groq (openai/gpt-oss-120b, streaming)
 ↓
Answer with [n] citations  ·  [DECLINED] refusals carry no sources
 ↓
Vue.js 3 (Library / Notebook / Knowledge Bytes)
```

## Backend layout (`backend/app/`)

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS, lifespan (runs migrations on boot, fail-fast if DB down) |
| `api/routes.py` | HTTP surface; thin — no SQL, no prompts inline |
| `pipeline.py` | Upload lifecycle: parse → chunk → embed → store → mark ready/failed (BackgroundTask) |
| `ingest.py` | Docling extraction (lazy import, injectable for tests) + overlapping chunker |
| `embeddings.py` | 384-dim embeddings; CPU-pinned model; deterministic mock for tests |
| `db.py` | All SQL in one place (psycopg3 pool); schema via `migrations/001_init.sql` |
| `retrieval.py` | Embed query → pgvector cosine search → threshold filter → context formatting |
| `llm.py` | Groq streaming client, system prompt, `[DECLINED]` helpers, mock mode |
| `knowledge_bytes.py` | Architecture-first 10-second explainer template + prompt builder |
| `config.py` | Pydantic-settings; `EMBEDDING_DIM` validated to always equal 384 |

## Key design decisions

1. **pgvector, not FAISS** — the assignment requires PostgreSQL + pgvector. Documents
   and vectors live together, so deletes cascade and metadata stays consistent.
   `ivfflat … vector_cosine_ops` indexes the ANN search; the app over-fetches
   (`top_k × 2`) then applies the similarity threshold in Python for exact control.

2. **Citations are structural, not hoped-for.** The context block is numbered
   `[1..n]`, the system prompt requires `[n]` markers per claim, and refusals must
   begin with `[DECLINED]`. The server consumes that marker from the token stream
   (peek-window) and suppresses sources for declined answers — the client can
   never show citations on a non-answer.

3. **Ingestion is async to the request.** `POST /api/documents` returns `202`
   immediately; a BackgroundTask parses/embeds/indexes while the frontend polls
   document status. A failed PDF becomes `status=failed` with the error — never a
   silent drop.

4. **Mock modes for offline work.** No `GROQ_API_KEY` → mock answers (clearly
   labeled in UI). `MOCK_EMBEDDINGS=true` → deterministic hash embeddings so the
   whole test suite runs without model downloads or network.

5. **Dedupe by content hash.** Re-uploading the same PDF returns `409` with the
   existing document instead of double-indexing.

6. **Docling is a lazy, injectable dependency.** `parse_pdf()` takes an optional
   `extractor`; tests inject fakes, production uses `DocumentConverter`. The heavy
   import never runs at module load.

## Data model

```sql
documents(id uuid, filename, title, page_count, chunk_count, char_count,
          file_size, sha256, status, error, created_at)
chunks(id uuid, document_id → documents ON DELETE CASCADE,
       chunk_index, page_start, page_end, content, embedding vector(384))
```

Indexes: `ivfflat (embedding vector_cosine_ops)` for ANN search, btree on
`chunks(document_id)`. Only `status='ready'` documents are searchable.

## Frontend layout (`frontend/src/`)

| File | Responsibility |
|---|---|
| `App.vue` | Shell: header, Library/Notebook tabs, mock-mode banner, polling loop |
| `components/UploadPanel.vue` | Drag-drop + picker upload, per-file status |
| `components/DocumentList.vue` | Library table with status badges + delete |
| `components/ChatPanel.vue` | Streaming chat, citation chips → excerpt viewer |
| `components/KnowledgeBytesModal.vue` | Paste code → streaming Knowledge Bytes |
| `services/api.js` | REST + hand-rolled SSE parsing (no extra deps) |

## Failure modes

| Failure | Behavior |
|---|---|
| DB unreachable at boot | App refuses to start (fail-fast in lifespan) |
| DB unreachable at runtime | `/api/health` → `degraded`; endpoints 500 with message |
| PDF unparsable | `status=failed` + error text; temp file removed |
| No relevant chunks | Immediate declined answer, no LLM call, no sources |
| Groq error mid-stream | `502` on sync; `event: error` on streams |
| Oversized upload | `413`; non-PDF `400`; duplicate `409` |

## Scaling notes (beyond MVP scope)

- Swap BackgroundTasks for a real queue (Celery/RQ) for multi-worker ingestion.
- Raise `ivfflat` lists / move to HNSW as chunk counts grow past ~1M.
- Add per-user scoping (`owner_id` on documents) for multi-tenancy.
- Cache embeddings of repeated chunk contents by content hash.
