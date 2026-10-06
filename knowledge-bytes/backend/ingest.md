# Knowledge Bytes: Document Ingestion

> Source: `backend/app/ingest.py`, `backend/app/pipeline.py`
>
> Covers:
> - `parse_pdf()` / `_docling_extract()` — PDF → text items with page numbers
> - `chunk_items()` — overlapping character chunker
> - `process_upload()` — the background pipeline (parse → embed → store → ready)

---

## Byte 1 — Docling: PDFs become text with page provenance

### Builds on
[Request Lifecycle](../architecture/request-lifecycle.md) (Byte 2).

### In plain terms
`ingest.py` uses Docling's `DocumentConverter` to turn a PDF into an ordered list of text items, each tagged with the page it came from. Page numbers survive all the way to citations because they're captured here, at the very first step.

### Relevant code
`backend/app/ingest.py`:

```python
def _docling_extract(pdf_path: str) -> ParsedDocument:
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document
    ...
    for element, _level in doc.iterate_items():
        txt = getattr(element, "text", None)
        if not txt or not txt.strip():
            continue
        page_no = None
        prov = getattr(element, "prov", None)
        if prov:
            page_no = getattr(prov[0], "page_no", None)
        items.append(TextItem(text=txt.strip(), page_no=page_no))
```

### What's happening
Docling iterates document elements in reading order; each element's `prov` (provenance) carries the page number. The code defensively handles missing provenance (`getattr` chains, `try/except`) — a PDF without page info still ingests, just without page citations. `parse_pdf()` wraps this and raises `ValueError` if *no* text was extracted at all (e.g. a scanned image PDF).

### Why it matters
Citations show "p. 3" because this function preserves page numbers. The `extractor` parameter on `parse_pdf()` lets tests inject a fake parser, so the chunker can be tested without Docling's heavy models.

---

## Byte 2 — Chunking: overlapping windows with page spans

### Builds on
Byte 1 (text items in reading order).

### In plain terms
`chunk_items()` greedily packs text items into ~1000-character chunks, carrying a 150-character overlap tail into the next chunk so concepts aren't split at boundaries. Each chunk records the min/max page of its items.

### Relevant code
```python
def chunk_items(items, chunk_size=None, chunk_overlap=None):
    ...
    def flush() -> None:
        content = " ".join(buf_parts).strip()
        if content:
            pages = [p for p in buf_pages if p is not None]
            chunks.append({
                "chunk_index": len(chunks),
                "content": content,
                "page_start": min(pages) if pages else None,
                "page_end": max(pages) if pages else None,
            })
        # carry overlap tail into the next chunk
        tail = content[-chunk_overlap:] if chunk_overlap else ""
        buf_parts = [tail] if tail else []
```

### What's happening
Items accumulate until adding the next would exceed `CHUNK_SIZE` (default 1000), then `flush()` emits a chunk and seeds the next buffer with the last 150 characters. Oversized single items are pre-split with the same overlap. `page_start`/`page_end` span the pages covered — a chunk drawn from pages 2–3 cites as "pp. 2–3".

### Why it matters
Chunking is the granularity of everything downstream: each chunk gets one embedding, one row, and potentially one citation. The overlap is a deliberate recall trade-off — slightly more storage, fewer "answer split across two chunks" failures.

---

## Byte 3 — `process_upload()`: the background pipeline

### Builds on
Bytes 1–2, [Embeddings](./embeddings.md), [Database](./db.md).

### In plain terms
`pipeline.py`'s `process_upload()` is the function the upload endpoint schedules as a background task. It runs parse → chunk → batch-embed → insert → mark-ready, converts any exception into a `failed` document row, and always deletes the temp file.

### Relevant code
`backend/app/pipeline.py`:

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
        try: os.remove(saved_path)
        except OSError: pass
```

### What's happening
Embeddings are computed in one batch call (`embed_texts` over all chunk contents — far faster than one-by-one), attached to the chunk dicts, and inserted with `ON CONFLICT (document_id, chunk_index) DO NOTHING` (idempotent). Success flips the row to `ready` with page/chunk/char counts; *any* failure — Docling crash, embedding error, DB hiccup — is caught, logged, and recorded as `failed` with the exception type and message (truncated to 2000 chars). The `finally` block removes the temp upload so disk never fills.

### Why it matters
This `try/except/finally` is the reason uploads can't leave the system in a stuck state: every document ends as `ready` or `failed`, never `processing` forever, and temp files never leak. The frontend's polling loop (`useLibrary`) watches exactly this transition.

---

## Putting It Together

Ingestion is three layers: `ingest.py` (pure functions: PDF → items → chunks, fully testable without Docling), `embeddings.py` (chunks → vectors), and `pipeline.py` (the orchestrator that ties them to the database with failure handling). The API route only validates and schedules; everything substantive happens in `process_upload`. Next: [Embeddings](./embeddings.md) (how text becomes vectors) and [Database](./db.md) (where vectors live).
