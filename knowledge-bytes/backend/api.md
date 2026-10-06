# Knowledge Bytes: API Routes

> Source: `backend/app/api/routes.py`
>
> Covers:
> - `upload_document()` — `POST /api/documents`
> - `list_documents()` / `delete_document()` — `GET`, `DELETE /api/documents`
> - `chat()` — `POST /api/chat` (SSE streaming)
> - `chat_sync()` — `POST /api/chat/sync`
> - `health()` — `GET /api/health`
> - `_stream_answer()` — refusal-safe SSE emission
> - `_to_source_out()` — citation payload shaping

---

## Byte 1 — The router is the whole HTTP surface

### Builds on
[System Overview](../architecture/system-overview.md).

### In plain terms
Every HTTP endpoint lives in one file, `backend/app/api/routes.py`, mounted at `/api`. There are six: upload, list, delete, streaming chat, sync chat, health. The file contains no SQL (that's `db.py`) and no ML (that's `retrieval.py`/`llm.py`) — it only validates input, calls the right module, and shapes the response.

### Relevant code
```python
router = APIRouter(prefix="/api")
settings = get_settings()

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[str] | None = Field(default=None, max_length=50)
```

### What's happening
A single `APIRouter` with Pydantic request models. `ChatRequest` is the contract the frontend must honor: a non-empty question, an optional `top_k` (1–20), and an optional `document_ids` list (≤50) that scopes retrieval to selected documents.

### Why it matters
If you want to know what the backend accepts, this file is the answer. `document_ids` here is the server-side enforcement behind the Notebook's document-scope selector.

---

## Byte 2 — Upload: validate, dedupe, defer

### Builds on
Byte 1 (router surface).

### In plain terms
`POST /api/documents` validates the file (PDF-only, ≤50 MB, non-empty), rejects byte-identical duplicates with `409`, saves the file to a temp path, creates a `processing` document row, and queues the real work as a background task — returning `202` immediately.

### Relevant code
```python
sha256 = hashlib.sha256(data).hexdigest()
existing = [d for d in db.list_documents() if d.get("sha256") == sha256 and d["status"] == "ready"]
if existing:
    raise HTTPException(status_code=409, detail="This PDF is already in your library")
...
doc = db.create_document(filename=name, title=name, file_size=len(data), sha256=sha256)
background_tasks.add_task(process_upload, str(doc["id"]), str(saved_path))
return {"id": str(doc["id"]), "filename": name, "status": "processing"}
```

### What's happening
Three guards run before anything is stored: extension/content-type check (`400`), size cap (`413`), and SHA-256 dedupe against `ready` documents (`409`). Only then is the row created and `process_upload` (in `pipeline.py`) scheduled. The client never waits for Docling.

### Why it matters
This is why the Library can show "processing" rows with live progress: the endpoint is deliberately thin, and the heavy pipeline runs after the response. See [Ingestion](./ingest.md) for what `process_upload` does.

---

## Byte 3 — Chat: retrieve first, then stream

### Builds on
Byte 1, [Retrieval](./retrieval.md).

### In plain terms
`POST /api/chat` runs retrieval *before* touching the LLM. If nothing passes the similarity threshold, it returns a canned refusal without calling Groq at all. Otherwise it streams the answer as Server-Sent Events.

### Relevant code
```python
hits = retrieve(question, top_k=req.top_k, document_ids=req.document_ids)
if not hits:
    def _declined():
        yield f"event: sources\ndata: {json.dumps({'sources': []})}\n\n"
        yield f"data: {json.dumps({'token': 'I couldn’t find anything...'})}\n\n"
        yield f"event: done\ndata: {json.dumps({'declined': True})}\n\n"
    return StreamingResponse(_declined(), media_type="text/event-stream")
return StreamingResponse(_stream_answer(question, hits), media_type="text/event-stream")
```

### What's happening
`retrieve()` returns thresholded hits (possibly scoped by `document_ids`). The empty case short-circuits: no model call, no cost, empty sources, `declined: true`. The non-empty case delegates to `_stream_answer`, which emits `sources` → `token`* → `done` events.

### Why it matters
The "no evidence, no LLM call" rule is the cheapest grounding guarantee in the system — it makes off-corpus questions fast (~0.1 s) and impossible to hallucinate on.

---

## Byte 4 — Refusal safety inside the stream

### Builds on
Byte 3 (chat streaming).

### In plain terms
`_stream_answer` watches the first characters of the model's output for the `[DECLINED]` marker. If the model refuses, the marker is consumed server-side (never streamed) and the `sources` event carries an empty list — so a refusal can never display citations, even if the model misbehaves.

### Relevant code
```python
if head.startswith(DECLINE_MARKER):
    declined, decided = True, True
    rest = head[len(DECLINE_MARKER):]
    buf = ""
    yield from emit_sources()  # declined -> no citations
    yield from emit(rest)
    continue
```

### What's happening
Tokens are buffered until the head either matches `[DECLINED]` exactly or provably diverges from it. Only after that decision is the `sources` event emitted — with real sources for answers, empty for refusals. The marker itself is stripped before anything reaches the client.

### Why it matters
This is defense in depth: the system prompt *asks* for `[DECLINED]`, but this code *enforces* the consequence. The frontend can trust `declined: true` to mean "show no sources."

---

## Byte 5 — What a source looks like on the wire

### Builds on
Byte 3.

### In plain terms
`_to_source_out()` converts raw DB hits into the citation payload: rank, document identity, page span, similarity score, and a 500-char excerpt. Ranks (`1…n`) are assigned here and become the `[n]` markers the model cites.

### Relevant code
```python
def _to_source_out(hits: list[dict]) -> list[dict]:
    return [
        {
            "rank": i,
            "document_id": str(h["document_id"]),
            "filename": h["filename"],
            "title": h["title"] or h["filename"],
            "chunk_index": h["chunk_index"],
            "page_start": h["page_start"],
            "page_end": h["page_end"],
            "similarity": round(float(h["similarity"]), 4),
            "excerpt": h["content"][:500],
        }
        for i, h in enumerate(hits, start=1)
    ]
```

### What's happening
Each hit gets a 1-based `rank` matching its position in the numbered context block (`[1] … [n]`) that `format_context()` builds. The excerpt is truncated to 500 chars to keep the SSE payload small; the full chunk text stays in Postgres.

### Why it matters
Ranks are the join key between three things: the context block the model sees, the `[n]` markers it emits, and the Sources panel the UI renders. Break this numbering and citations break.

---

## Putting It Together

`routes.py` is a thin orchestration layer: validate → `db`/`retrieval`/`llm`/`pipeline` → shape the response. Upload defers work to a background task; chat retrieves before generating and enforces refusal semantics in the stream itself. The sync variant (`POST /api/chat/sync`) runs the same logic without SSE for tests and simple clients. Next: [Database](./db.md) (what's stored), [Retrieval](./retrieval.md) (how questions find chunks), [LLM](./llm.md) (how answers are generated).
