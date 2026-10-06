# Vector-Brain Knowledge Bytes

Knowledge Bytes are a guided walkthrough of the **actual Vector-Brain codebase**.
They break important modules and responsibilities into small, progressive
explanations — each grounded in real source files with real code snippets — so a
developer can understand the system without reverse-engineering the repository
from scratch.

> These documents describe the current implementation. They are **developer
> documentation**, not an application feature: there is no Knowledge Bytes page,
> API endpoint, or database table in the running app.
>
> The *method* used to write them is defined separately in
> [knowledge-bytes-prompt.md](knowledge-bytes-prompt.md) (kept as a reusable
> reference). Everything else in this directory is the *result* of applying that
> method to Vector-Brain's source code.

## Start Here

1. [System Overview](architecture/system-overview.md) — the two programs, the database, configuration, and startup.
2. [Request Lifecycle](architecture/request-lifecycle.md) — the write path (PDF → vectors) and the read path (question → cited answer).

## Backend (`backend/app/`)

| Byte | Source file(s) |
|---|---|
| [API](backend/api.md) | `api/routes.py` — endpoints, SSE streaming, refusal safety |
| [Configuration](backend/config.md) | `config.py` — settings, the 384-dimension contract, mock modes |
| [Database](backend/db.md) | `db.py`, `migrations/001_init.sql` — Postgres + pgvector schema and search |
| [Ingestion](backend/ingest.md) | `ingest.py`, `pipeline.py` — Docling parse, chunking, background pipeline |
| [Embeddings](backend/embeddings.md) | `embeddings.py` — MiniLM vectors, thread-safe loading, mock path |
| [Retrieval](backend/retrieval.md) | `retrieval.py` — cosine search, thresholding, numbered context |
| [LLM](backend/llm.md) | `llm.py` — Groq streaming, system prompt, `[DECLINED]` contract |

## Frontend (`frontend/src/`)

| Byte | Source file(s) |
|---|---|
| [Architecture](frontend/architecture.md) | `main.js`, `App.vue`, `AppSidebar.vue` — view switching, shell, theming |
| [API Services](frontend/services.md) | `services/api.js` — REST helpers, SSE parsing |
| [Library & Upload](frontend/library.md) | `LibraryView.vue`, `UploadModal.vue`, `useLibrary.js` |
| [Notebook](frontend/notebook.md) | `NotebookView.vue` — chat, scoping, cited-only sources, history |
| [Composables](frontend/composables.md) | `usePrefs.js`, `useTheme.js`, `useToasts.js`, `utils/format.js` |

## Source-code map

Every byte names the exact file(s) it explains and quotes only short, relevant
excerpts — never whole files. Cross-module connections are called out inline
(e.g. how `routes.py` calls `retrieval.py`, how `NotebookView.vue` consumes
`services/api.js`), and [Request Lifecycle](architecture/request-lifecycle.md)
traces both end-to-end flows.

## Methodology & examples

- [knowledge-bytes-prompt.md](knowledge-bytes-prompt.md) — the reusable Knowledge Bytes methodology.
- [examples/example.md](examples/example.md) — a generic worked example of the format.

## Maintenance note

These bytes describe the implementation as of the commit they were written
against. If the code changes, the affected byte should be updated to match —
each byte's header lists its source file(s) to make that easy. There is no
automated generation; quality comes from keeping the bytes close to the code.
