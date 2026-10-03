# Vector-Brain — Demo Script (5 minutes)

A scripted walkthrough for evaluators. Assumes the app is running
(see README Quickstart).

## 0:00 — The idea (30s)

> "Vector-Brain is a Notebook-LLM-lite: a second brain for studying. You upload
> PDFs, ask questions across all of them, and get answers with citations to the
> exact passages. Knowledge Bytes explains code in 10-second architecture-first
> chunks."

## 0:30 — Upload (60s)

1. Open the **Library** tab.
2. Drag in 2–3 PDFs (e.g. lecture notes from different chapters).
3. Point out: status flips `processing → ready`, chunk/page counts appear.
4. Re-upload the same PDF → it is rejected as a duplicate (sha256 dedupe).

## 1:30 — Ask across documents (90s)

1. Switch to the **Notebook** tab.
2. Ask a question that spans two PDFs, e.g.
   *"How does backpropagation relate to gradient descent?"*
3. Watch the answer stream in with **[1] [2]** citation chips.
4. Click a chip → the exact excerpt, page number and similarity score appear.
5. Ask something the PDFs don't cover → the assistant declines plainly and
   **no citations are shown** (refusals never carry sources).

## 3:00 — Knowledge Bytes (60s)

1. Click **⚡ Knowledge Bytes** in the header.
2. Paste ~40 lines of code (e.g. the chunker from this repo), set language.
3. **Generate** → BYTE 1…N stream in: ROLE / FLOW / CONNECTS TO / WHY / KEY CODE,
   ending with PUTTING IT TOGETHER.

## 4:00 — Under the hood (60s)

1. Open `/api/health` → `groq_mode`, document/chunk counts.
2. Open `/docs` → try `POST /api/chat/sync` and `POST /api/knowledge-bytes`.
3. Mention the pipeline (footer of the app):
   PDFs → Docling → 384-dim embeddings → PostgreSQL + pgvector → Groq.

## Talking points for Q&A

- **Why pgvector?** Documents and vectors in one store; deletes cascade;
  `ivfflat` cosine index for ANN search.
- **Why 384 dims?** all-MiniLM-L6-v2; the schema (`vector(384)`) and config
  (`EMBEDDING_DIM`) are cross-validated so they can't drift apart.
- **How are citations trustworthy?** Numbered context blocks + a system prompt
  that requires `[n]` markers; `[DECLINED]` refusals are detected server-side
  and suppress sources.
- **Offline?** Mock Groq mode + mock embeddings run the whole suite and the UI
  with zero keys and zero downloads.
