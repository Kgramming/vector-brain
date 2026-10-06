# 08 — End to End

Follow a PDF and a question through the whole app, and learn where to look when something breaks.

**Builds on:** `01`–`07`

---

### Byte 1: You upload a PDF

**Builds on:** `02`, `05`, `07` (Byte 3)

**In plain terms:**
You pick a file in `UploadModal`. `XMLHttpRequest` POSTs to `/api/documents`; the backend checks it's a PDF under 50 MB, rejects duplicates by SHA-256 (`409`), creates a `processing` row, and returns `202`. A `BackgroundTask` runs `process_upload()`: Docling extracts text with page numbers, the chunker windows it with overlap, MiniLM embeds the chunks in one batch, `db.py` inserts them, the row flips to `ready`. The Library polls `status` and the card appears.

**The code:**
```text
UploadModal → POST /api/documents → 202 → process_upload()
    Docling → chunk_items() → embed_texts() → insert_chunks() → mark_document_ready()
                                                        documents: processing → ready
```

---

### Byte 2: You ask a question

**Builds on:** `03`, `04`, `07` (Byte 2)

**In plain terms:**
You type in NotebookView and hit send. `streamChat()` POSTs the question with the selected `document_ids`. The backend embeds it, runs the cosine search (scoped to your selection, `ready`-only), thresholds at 0.30, trims to top-K, and numbers the survivors `[1]…[n]`. If none survive, you get a refusal with no sources and no Groq call. Otherwise Groq streams a cited answer; the UI shows sources first, filters them to the cited ranks, and saves the conversation.

**The code:**
```text
NotebookView → POST /api/chat → retrieve() → no hits? declined, no sources
                                          → hits? stream_chat() (Groq SSE)
                                              → event: sources → event: token* → event: done
```

---

### Byte 3: Where to look if it breaks

**Builds on:** Bytes 1–2

**In plain terms:**
Upload rejected? `routes.py` validation or the SHA-256 dedupe. Stuck on `processing`? Check the `error` column on the `documents` row — `pipeline.py` records it. Blank answer? `retrieve()` found nothing above 0.30 — lower `top_k` won't help, the threshold is in `config.py`. Wrong citations? `format_context()` numbering vs. `_to_source_out()` ranks (`04`, Byte 4). Conversation missing after refresh? `localStorage` key `conversations`. Slow answer? Retrieval is milliseconds (`search_chunks` on the ivfflat index) — the time is Groq's streaming.

---

## PUTTING IT TOGETHER

Two flows run the whole product. **Write:** upload → Docling → chunk → embed → pgvector. **Read:** embed question → cosine search → threshold → prompt → stream with citations. The database is the only shared state; the frontend is stateless views over HTTP; every setting that matters lives in `config.py`. Start at the symptom, walk the chain, and the layer where the data goes wrong is the layer with the bug.
