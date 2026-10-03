# Vector-Brain — API Reference

Base URL (dev): `http://localhost:8000` · Interactive docs: `/docs`

All `/api/*` responses are JSON unless noted. Errors use FastAPI's
`{"detail": "..."}` shape.

## GET /api/health

Service and dependency status.

```json
{
  "status": "ok | degraded",
  "groq_mode": "live | mock",
  "documents": 3,
  "chunks": 128,
  "db_error": null
}
```

## Documents

### POST /api/documents — upload a PDF

Multipart form, field `file`. Returns `202` immediately; ingestion runs in the
background — poll `GET /api/documents` for `status: ready`.

```json
{ "id": "uuid", "filename": "notes.pdf", "status": "processing" }
```

| Code | Meaning |
|---|---|
| 400 | Not a PDF / empty file |
| 409 | Same PDF (sha256) already indexed |
| 413 | Larger than `MAX_UPLOAD_MB` |

### GET /api/documents

```json
{ "documents": [
  { "id": "uuid", "filename": "notes.pdf", "title": "notes.pdf",
    "page_count": 24, "chunk_count": 61, "char_count": 58210,
    "file_size": 1048576, "status": "ready | processing | failed",
    "error": null, "created_at": "2026-10-03T…" }
]}
```

### DELETE /api/documents/{id}

Deletes the document and all its chunks (`ON DELETE CASCADE`). `404` if unknown.
Returns `{ "deleted": "uuid" }`.

## Chat

### POST /api/chat — streaming answer (SSE)

Body: `{ "question": "…", "top_k": 6 }` (`top_k` optional, 1–20).

Event stream:

```
event: sources
data: {"sources": [{"rank":1,"document_id":"…","filename":"notes.pdf","title":"…",
        "chunk_index":4,"page_start":3,"page_end":3,"similarity":0.82,
        "excerpt":"first 500 chars…"}]}

data: {"token": "Photosynthesis "}
data: {"token": "happens …"}

event: done
data: {"declined": false}
```

- If no chunks pass the similarity threshold, the server skips the LLM and
  streams a declined answer with `"declined": true` and empty sources.
- If the model refuses (`[DECLINED]`), the marker is consumed server-side and
  `done` carries `"declined": true` — clients must hide citations then.
- Mid-stream Groq failures arrive as `event: error` with `{"detail": "…"}`.

### POST /api/chat/sync — non-streaming answer

Same body. Response:

```json
{
  "answer": "…with [1] citations…",
  "declined": false,
  "sources": [ /* same shape as SSE sources, [] when declined */ ]
}
```

## Knowledge Bytes

### POST /api/knowledge-bytes — streaming explainer (SSE)

Body: `{ "content": "…code or technical text…", "language": "python", "context_note": "auth module" }`
(`language`/`context_note` optional; `content` max 60k chars.)

Streams `data: {"token": "…"}` events in the architecture-first format:

```
BYTE N — <Component / Function / Responsibility>
ROLE: …
FLOW: Input → Processing → Output
CONNECTS TO: …
WHY: …
KEY CODE: …
…
PUTTING IT TOGETHER
…
```

In mock mode (no `GROQ_API_KEY`) it streams the format skeleton so the UI stays
usable. Empty content → `422`.
