# Vector-Brain — Demo Script (5 minutes)

A scripted walkthrough for evaluators. Assumes the app is running
(see README Quickstart). Demo PDFs live in `demo-pdfs/`.

## 0:00 — The idea (30s)

> "Vector-Brain is a Notebook-LLM-lite: a second brain for studying. You upload
> PDFs, ask questions across all of them, and get answers with citations to the
> exact passages — page numbers included."

Point at the **Home** dashboard: live stats (documents, pages, chunks).

## 0:30 — Upload (60s)

1. Click **Add Documents** (or Library → Upload PDF).
2. Drag in the three PDFs from `demo-pdfs/`.
3. Point out the pipeline: Uploading → Parsing with Docling → Creating chunks →
   Generating embeddings → Indexing in PostgreSQL → Ready.
4. Re-upload one PDF → rejected as a duplicate (sha256 dedupe, 409).

## 1:30 — Ask across documents (90s)

1. Open the **Notebook**.
2. Ask a cross-document question, e.g.
   *"How does backpropagation relate to gradient descent?"*
3. Watch the answer stream with clickable **[1] [2]** citations.
4. Click a citation → the **Sources** panel highlights the passage: filename,
   page, relevance bar, excerpt.
5. Uncheck a document in **Search across** → the answer is scoped to the
   remaining docs (`document_ids` filtering, server-side).
6. Ask something the PDFs don't cover → the assistant declines plainly and
   **no citations are shown** (refusals never carry sources).

## 3:00 — Library & personalization (60s)

1. **Library**: toggle grid/list, search, sort by pages, star a favorite.
2. **Settings → Appearance**: switch to Midnight theme + a different accent —
   the whole app re-themes instantly.

## 4:00 — Under the hood (60s)

1. Open `/api/health` → `groq_mode`, document/chunk counts.
2. Open `/docs` → try `POST /api/chat/sync` with `document_ids`.
3. Mention the pipeline: Docling → 384-dim MiniLM → pgvector cosine search →
   Groq streaming → cited answers.

## Suggested questions (all answerable from demo-pdfs/)

- "Compare precision and recall — when does each matter?"
- "What is overfitting and how do you detect it?"
- "Explain backpropagation in simple terms."
- "What is the bias-variance tradeoff?"
- "How do CNNs differ from plain feedforward networks?"
