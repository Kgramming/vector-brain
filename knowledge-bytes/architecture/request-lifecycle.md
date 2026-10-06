# Knowledge Bytes: Request Lifecycle

> Source: `frontend/src/services/api.js`, `backend/app/api/routes.py`, `backend/app/pipeline.py`, `backend/app/retrieval.py`, `frontend/src/views/NotebookView.vue`
>
> Covers:
> - The upload → ingest → indexed flow (write path)
> - The question → retrieve → stream → cite flow (read path)

---

## Byte 1 — The two lifecycles

### Builds on
[System Overview](./system-overview.md).

### In plain terms
Vector-Brain has two independent flows. The **write path** turns an uploaded PDF into searchable vectors (slow, background). The **read path** turns a question into a streamed, cited answer (fast, synchronous-ish). They meet only in PostgreSQL.

### Relevant code
Write path entry — `backend/app/api/routes.py`:

```python
@router.post("/documents", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    ...
    doc = db.create_document(filename=name, title=name, file_size=len(data), sha256=sha256)
    background_tasks.add_task(process_upload, str(doc["id"]), str(saved_path))
    return {"id": str(doc["id"]), "filename": name, "status": "processing"}
```

Read path entry — same file:

```python
@router.post("/chat")
def chat(req: ChatRequest):
    ...
    hits = retrieve(question, top_k=req.top_k, document_ids=req.document_ids)
    ...
    return StreamingResponse(_stream_answer(question, hits), media_type="text/event-stream")
```

### What's happening
Upload returns **202 Accepted** immediately with `status: "processing"`; the heavy work (`process_upload`) runs as a FastAPI `BackgroundTask`. Chat runs `retrieve()` inline, then returns a **streaming SSE response**. The frontend polls document status while ingestion runs, and consumes the SSE token stream for answers.

### Why it matters
This split is the core UX contract: uploads never block the UI, and answers start streaming as soon as the first token arrives. Everything below is a detail of one of these two paths.

---

## Byte 2 — Write path: PDF to vectors

### Builds on
Byte 1 (the two lifecycles).

### In plain terms
An uploaded PDF goes: validation → SHA-256 dedupe → saved to disk → Docling parse → overlapping chunks → 384-dim embeddings → Postgres → marked `ready`. Any failure marks the document `failed` with the error recorded.

### Relevant code
`backend/app/pipeline.py` — the whole pipeline in one function:

```python
def process_upload(doc_id: str, saved_path: str) -> None:
    try:
        parsed, chunks = ingest_pdf(saved_path)
        vectors = embed_texts([c["content"] for c in chunks])
        for chunk, vec in zip(chunks, vectors):
            chunk["embedding"] = vec
        db.insert_chunks(doc_id, chunks)
        db.mark_document_ready(doc_id, parsed.page_count, len(chunks), char_count)
    except Exception as exc:
        db.mark_document_failed(doc_id, f"{type(exc).__name__}: {exc}")
    finally:
        os.remove(saved_path)  # temp file always cleaned up
```

### What's happening
`ingest_pdf` (Docling → text items with page numbers → overlapping 1000-char chunks) produces chunks; `embed_texts` batch-embeds them with `all-MiniLM-L6-v2`; `insert_chunks` writes them with their vectors; the document flips to `ready`. The `try/except` guarantees a failed PDF becomes a visible `failed` row instead of a stuck `processing` one, and the temp file is always deleted.

### Why it matters
This is the only place vectors are created. The read path never embeds documents — it only embeds the *question* and compares. If ingestion is understood, the database contents are understood.

---

## Byte 3 — Read path: question to cited answer

### Builds on
Byte 1 (the two lifecycles), Byte 2 (what's in the database).

### In plain terms
A question is embedded, pgvector finds the most similar chunks (filtered to the selected documents, thresholded by similarity), the chunks become a numbered context block, Groq answers with `[n]` citations, and the answer streams back over SSE — sources first, then tokens.

### Relevant code
`backend/app/api/routes.py` — the chat endpoint's decision points:

```python
hits = retrieve(question, top_k=req.top_k, document_ids=req.document_ids)
if not hits:
    # No evidence: answer the refusal path without calling the model.
    def _declined():
        yield f"event: sources\ndata: {json.dumps({'sources': []})}\n\n"
        yield f"data: {json.dumps({'token': 'I couldn’t find anything...'})}\n\n"
        yield f"event: done\ndata: {json.dumps({'declined': True})}\n\n"
    return StreamingResponse(_declined(), media_type="text/event-stream")
return StreamingResponse(_stream_answer(question, hits), media_type="text/event-stream")
```

### What's happening
Three branches: (1) no hits → instant refusal, **no LLM call**, empty sources; (2) hits → stream; (3) inside the stream, a `[DECLINED]` prefix from the model suppresses citations server-side so a refusal can never carry sources. The frontend (`services/api.js` → `streamChat`) parses the SSE events into `onSources` / `onToken` / `onDone` callbacks.

### Why it matters
Grounding is enforced at three layers: retrieval thresholding (only similar-enough chunks), the system prompt (`[DECLINED]` marker + `[n]` citation rules), and server-side refusal handling. The frontend additionally filters the Sources panel to exactly the citations the answer emitted.

---

## Byte 4 — Where the paths meet: PostgreSQL

### Builds on
Bytes 2 and 3.

### In plain terms
Both paths touch the same two tables. The write path inserts into `documents` and `chunks`; the read path joins them for similarity search. `ON DELETE CASCADE` keeps them consistent.

### Relevant code
`backend/migrations/001_init.sql` (essentials):

```sql
CREATE TABLE documents ( ... status TEXT NOT NULL DEFAULT 'processing', ... );
CREATE TABLE chunks (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ...
    embedding vector(384) NOT NULL,
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX chunks_embedding_ivfflat_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### What's happening
`documents` tracks lifecycle (`processing` → `ready`/`failed`); `chunks` holds the text, page spans, and 384-dim vectors. The `ivfflat` index accelerates cosine nearest-neighbor search; deleting a document automatically deletes its chunks.

### Why it matters
There is no cache, no queue, no secondary store. If you can read these two tables, you can see exactly what the system knows — which is why the write path's `mark_document_ready` / `mark_document_failed` transitions are the system's heartbeat.

---

## Putting It Together

A PDF travels **upload → validate → dedupe → Docling → chunk → embed → pgvector → ready** (background, polled). A question travels **embed → pgvector cosine search → threshold → numbered context → Groq → SSE tokens → cited answer** (streaming, sources-first). PostgreSQL is the single rendezvous point. The backend bytes below open each stage; the frontend bytes show how the UI drives them.
