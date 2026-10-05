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

---

## Optional: public demo via ngrok

To show Vector-Brain to someone without them installing anything, expose the
app publicly with [ngrok](https://ngrok.com/). The architecture is:

```
                    ┌─────────────────────┐
  reviewer ────────▶│ ngrok → Vite (5173) │──▶ ngrok → FastAPI (8000)
  (browser)         └─────────────────────┘         │
                                              ┌────▼──────────────┐
                                              │ PostgreSQL+pgvector│
                                              │  stays LOCAL —     │
                                              │  never exposed     │
                                              └───────────────────┘
```

**PostgreSQL must remain local.** Only the frontend and the backend are
exposed; the database is reachable solely from the machine running the
backend. Never tunnel port 5432.

### Steps

1. Start the stack locally (database + backend + frontend) as in the README.
2. In one terminal, expose the backend:
   ```bash
   ngrok http 8000
   ```
   Note the public URL, e.g. `https://<id>.ngrok-free.app`.
3. Point the frontend at the **public backend URL**. The Vite dev server reads
   it from the environment — set it before `npm run dev`:
   ```bash
   # frontend/.env
   VITE_API_URL=https://<id>.ngrok-free.app
   ```
   (Without this, the browser page served from the public frontend URL would
   try to reach `localhost:8000` — your reviewer's own machine — and fail.)
4. Expose the frontend:
   ```bash
   ngrok http 5173
   ```
5. Share the frontend's ngrok URL. The reviewer uploads PDFs and chats;
   traffic flows reviewer → frontend tunnel → backend tunnel → local
   PostgreSQL.

### Notes

- Use `MOCK_EMBEDDINGS=false` (real MiniLM) for a genuine demo; ingestion is
  slower on first run while Docling fetches its models.
- Uploads are capped at `MAX_UPLOAD_MB` (default 50) — suitable for a demo.
- Do not commit ngrok URLs, authtokens, or tunnel credentials to the repo.
  Keep them in local shell history / environment only.
- For a persistent public demo, prefer a small VPS over a laptop tunnel.
