# Knowledge Bytes: System Overview

> Source: `backend/app/main.py`, `backend/app/config.py`, `docker-compose.yml`, `frontend/src/main.js`
>
> Covers:
> - Application bootstrap (`create_app()`, `lifespan`)
> - Configuration (`Settings`, `get_settings()`)
> - Service topology (FastAPI, PostgreSQL + pgvector, Vue frontend)

---

## Byte 1 — The system in one picture

### Builds on
Nothing — start here.

### In plain terms
Vector-Brain is two programs plus a database: a **FastAPI backend** that ingests PDFs and answers questions, a **Vue 3 frontend** that renders the UI, and **PostgreSQL 16 with pgvector** that stores both document metadata and embedding vectors.

### Relevant code
`backend/app/main.py` — the backend entrypoint:

```python
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        ...
    )
    app.include_router(router)
```

`docker-compose.yml` — the database:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: vectorbrain-postgres
    ports:
      - "5432:5432"
```

### What's happening
`create_app()` builds the FastAPI application: it loads settings, enables CORS for the Vite dev servers (`localhost:5173/5174`), and mounts the API router. The database is a stock `pgvector/pgvector:pg16` container — no custom image, just Postgres with the vector extension available.

### Why it matters
Every other byte hangs off this topology. The backend owns all RAG logic; the frontend is a thin client that calls HTTP endpoints; Postgres is the single source of truth for documents, chunks, and vectors. There is no separate vector database and no message queue.

---

## Byte 2 — Configuration: everything from the environment

### Builds on
Byte 1 (system topology).

### In plain terms
All backend settings live in one `Settings` class populated from environment variables. No secrets are hard-coded; an empty `GROQ_API_KEY` switches the backend into mock mode.

### Relevant code
`backend/app/config.py`:

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain"
    GROQ_API_KEY: str = ""  # empty => MOCK_GROQ mode (offline/dev)
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    TOP_K: int = 6
    SCORE_THRESHOLD: float = 0.30
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_MB: int = 50

    @property
    def mock_groq(self) -> bool:
        return not self.GROQ_API_KEY.strip()
```

### What's happening
`pydantic-settings` reads `.env` (or the process environment) into typed fields. Two properties derive behavior: `mock_groq` (no key → canned answers, no network) and `max_upload_bytes` / `cors_origin_list` (derived conveniences). A validator rejects any `EMBEDDING_DIM` other than 384, because the pgvector column is `vector(384)` — the model and the schema must agree.

### Why it matters
These numbers are the system's tuning surface: chunk size, retrieval depth, the similarity cutoff, upload limits. When you read later bytes, every "magic number" (top_k × 2 over-fetch, 0.30 threshold) comes from here. `get_settings()` is `lru_cache`d, so the whole backend shares one instance.

---

## Byte 3 — Startup: migrations before traffic

### Builds on
Byte 1 (bootstrap), Byte 2 (settings).

### In plain terms
Before the backend accepts any request, it applies the SQL migrations. If Postgres or pgvector is unreachable, the app fails fast at boot instead of serving 500s later.

### Relevant code
`backend/app/main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Fail fast on boot if the database (or pgvector) is unreachable —
    # better than serving 500s on the first request.
    db.run_migrations()
    yield
    db.close_pool()
```

### What's happening
The `lifespan` handler runs `db.run_migrations()` (which executes every `*.sql` file in `backend/migrations/`, idempotently via `IF NOT EXISTS`) before yielding — i.e., before the server starts accepting traffic. On shutdown it closes the connection pool.

### Why it matters
Schema and code can never drift: a fresh `docker-compose up` followed by `uvicorn` always produces a working database. This is also why the backend has no separate "setup" step.

---

## Byte 4 — The frontend boots from one file

### Builds on
Byte 1 (two programs + database).

### In plain terms
The Vue app starts in `frontend/src/main.js`: it applies the persisted theme before first paint (to avoid a flash), then mounts the root `App` component.

### Relevant code
`frontend/src/main.js`:

```js
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { useTheme } from './composables/useTheme.js'

// Apply persisted theme/accent/density before first paint (no flash).
useTheme().apply()

createApp(App).mount('#app')
```

### What's happening
Three lines do the work: import the root component and global styles, synchronously apply the saved theme (Light/Dark/Midnight/High-Contrast + accent) from localStorage, then mount. `App.vue` owns the sidebar, the current view (`home`/`library`/`notebook`/…), and the upload modal.

### Why it matters
There is no Vue Router — navigation is a `view` ref in `App.vue` switching between view components with `v-if`. All client state (theme, chat history, favorites) lives in composables backed by localStorage; the backend is stateless between requests.

---

## Putting It Together

Vector-Brain is a deliberately small system: one FastAPI process (configured entirely by environment), one Postgres+pgvector container (migrated automatically at boot), and one Vue SPA (no router, localStorage-backed UI state). The backend does everything "smart" — parsing, chunking, embedding, retrieval, LLM calls — while the frontend renders views and streams answers. The next byte-set, [Request Lifecycle](./request-lifecycle.md), traces a PDF and a question through every stage.
