# 02 — Ingestion Flow

Follow a PDF from upload to searchable vectors. When a document is stuck on "processing", this is where to look.

Source files in this byte: `backend/app/api/routes.py` (`upload_document`), `backend/app/pipeline.py` (`process_upload`), `backend/app/ingest.py` (`parse_pdf`, `chunk_items`), `backend/app/embeddings.py` (`embed_texts`)

---

### Byte 1: Upload validates, dedupes, then defers

**Builds on:** `01`

**In plain terms:**
`POST /api/documents` checks the file (PDF-only, ≤50 MB, non-empty), rejects byte-identical duplicates with `409` (SHA-256), saves the bytes to a temp path, creates a `processing` row, and queues the real work as a FastAPI `BackgroundTask` — returning `202` immediately. The UI never waits for Docling.

**The code:**
```text
Browser → POST /api/documents → validate → SHA-256 dedupe → 202 + BackgroundTask
                                                              ↓
                                              process_upload() in backend/app/pipeline.py
```

**The code:**
```python
sha256 = hashlib.sha256(data).hexdigest()
existing = [d for d in db.list_documents() if d.get("sha256") == sha256 and d["status"] == "ready"]
if existing:
    raise HTTPException(status_code=409, detail="This PDF is already in your library")
```

---

### Byte 2: Docling turns the PDF into text with page numbers

**Builds on:** Byte 1

**In plain terms:**
`ingest.py`'s `_docling_extract()` runs Docling's `DocumentConverter` and collects text elements in reading order, each tagged with its page from the element's `prov` (provenance). Page numbers survive all the way to citations because they're captured here, at the first step. A PDF with no extractable text raises `ValueError`.

**The code:**
```python
# backend/app/ingest.py
for element, _level in doc.iterate_items():
    txt = getattr(element, "text", None)
    ...
    prov = getattr(element, "prov", None)
    if prov:
        page_no = getattr(prov[0], "page_no", None)
    items.append(TextItem(text=txt.strip(), page_no=page_no))
```

The defensive `getattr` chains mean a PDF without page info still ingests — just without page citations.

---

### Byte 3: Chunking keeps concepts whole

**Builds on:** Byte 2

**In plain terms:**
`chunk_items()` greedily packs text into ~1000-character chunks, carrying a 150-character overlap tail into the next chunk so ideas aren't split at boundaries. Each chunk records the min/max page of its items (`page_start`/`page_end`).

**The code:**
```python
# backend/app/ingest.py — inside chunk_items()
tail = content[-chunk_overlap:] if chunk_overlap else ""  # overlap into next chunk
buf_parts = [tail] if tail else []
```

Chunking is the granularity of everything downstream: one chunk → one embedding → one row → potentially one citation.

---

### Byte 4: Text becomes vectors, then rows

**Builds on:** Byte 3

**In plain terms:**
`process_upload()` batch-embeds all chunk contents with `all-MiniLM-L6-v2` (384 dims, CPU, loaded lazily and thread-safely), attaches the vectors, inserts them into Postgres, and marks the document `ready`. Any exception becomes a `failed` row with the error recorded; the temp file is always deleted.

**The code:**
```python
# backend/app/pipeline.py
parsed, chunks = ingest_pdf(saved_path)
vectors = embed_texts([c["content"] for c in chunks])  # one batch call
for chunk, vec in zip(chunks, vectors):
    chunk["embedding"] = vec
db.insert_chunks(doc_id, chunks)
db.mark_document_ready(doc_id, parsed.page_count, len(chunks), char_count)
```

**The code:**
```python
# backend/app/embeddings.py — the model loads once, safely
_model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")  # inside a lock
```

The `try/except/finally` around all of this is why uploads can't get stuck: every document ends as `ready` or `failed`, never `processing` forever.

---

## PUTTING IT TOGETHER

Upload validates and defers; Docling extracts text with page provenance; the chunker windows it with overlap; MiniLM embeds it; Postgres stores it. The frontend's `UploadModal` shows this as staged progress by polling the `status` column that `process_upload` writes. `05` covers the tables, `03` covers what happens when you ask a question.
