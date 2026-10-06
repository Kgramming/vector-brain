# 01 — System Architecture

One mental picture for the whole app: two programs plus a database, and every feature is a trip between them.

Source files in this byte: `backend/app/main.py`, `backend/app/config.py`, `docker-compose.yml`, `frontend/src/main.js`

---

### Byte 1: Two programs and a database

**Builds on:** None — starting point

**In plain terms:**
Vector-Brain is a FastAPI backend (does everything smart), a Vue 3 frontend (renders everything), and PostgreSQL 16 with pgvector (stores everything). The backend owns parsing, embeddings, retrieval, and LLM calls; the frontend is a thin client over HTTP; Postgres holds documents, chunks, and vectors in one place.

**The code:**
```text
Vue frontend  →  HTTP/SSE  →  FastAPI backend  →  PostgreSQL + pgvector
   (views)                      (RAG logic)          (documents + vectors)
```

**The code:**
```python
# backend/app/main.py — the backend is built here
app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
app.include_router(router)   # all endpoints live in backend/app/api/routes.py
```

If you memorize this triangle, you can place every file: `backend/app/` is the backend, `frontend/src/` is the UI, and there is no separate vector database or message queue.

---

### Byte 2: One file holds every setting

**Builds on:** Byte 1

**In plain terms:**
`backend/app/config.py` defines a single `Settings` class with every tunable — database URL, Groq key/model, embedding model, top-K, similarity threshold, chunk size, upload limit. Values come from the environment; an empty `GROQ_API_KEY` switches the backend to mock mode.

**The code:**
```python
# backend/app/config.py
TOP_K: int = 6
SCORE_THRESHOLD: float = 0.30   # minimum cosine similarity to count as evidence
CHUNK_SIZE: int = 1000
EMBEDDING_DIM: int = 384        # must match the pgvector column — enforced below

@field_validator("EMBEDDING_DIM")
def dim_must_match_schema(cls, v):
    if v != 384:
        raise ValueError("EMBEDDING_DIM must be 384 (pgvector schema is vector(384))")
```

The validator is the interesting part: model output, setting, and SQL column must all agree on 384, and the app refuses to boot otherwise. When debugging behavior, check these numbers first — every "magic number" in retrieval comes from here.

---

### Byte 3: The database migrates itself at boot

**Builds on:** Bytes 1–2

**In plain terms:**
Before accepting traffic, the backend applies `backend/migrations/*.sql` (idempotent — `IF NOT EXISTS` everywhere). If Postgres or pgvector is unreachable, the app fails fast instead of serving 500s later. The database itself is a stock `pgvector/pgvector:pg16` container from `docker-compose.yml` — no custom image.

**The code:**
```python
# backend/app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.run_migrations()   # schema always matches the code
    yield
    db.close_pool()
```

---

### Byte 4: The frontend has no router

**Builds on:** Byte 1

**In plain terms:**
`frontend/src/main.js` applies the saved theme before first paint, then mounts `App.vue`. Navigation is a `view` ref (`home`/`library`/`notebook`/…) switching components with `v-if` — there is no Vue Router. State that must survive navigation (chat history, theme, favorites) lives in composables backed by localStorage.

**The code:**
```js
// frontend/src/main.js
useTheme().apply()              // no theme flash
createApp(App).mount('#app')
```

---

## PUTTING IT TOGETHER

One FastAPI process (configured by environment, migrated at boot), one Postgres+pgvector container, one Vue SPA (no router, localStorage-backed UI state). The backend does everything smart; the frontend renders views and streams answers. `02` walks a PDF through ingestion, `03`–`04` walk a question through retrieval and answering.
