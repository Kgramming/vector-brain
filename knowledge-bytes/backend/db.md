# Knowledge Bytes: Database (PostgreSQL + pgvector)

> Source: `backend/app/db.py`, `backend/migrations/001_init.sql`
>
> Covers:
> - Schema: `documents` and `chunks` tables
> - `vector(384)` storage and the `ivfflat` cosine index
> - `search_chunks()` — the similarity query
> - Connection pooling and migrations

---

## Byte 1 — Two tables, one relationship

### Builds on
[Request Lifecycle](../architecture/request-lifecycle.md) (Byte 4).

### In plain terms
Postgres holds two tables: `documents` (one row per uploaded PDF, with lifecycle status) and `chunks` (one row per text chunk, with its embedding vector). Chunks reference their document with `ON DELETE CASCADE` — deleting a PDF deletes its vectors automatically.

### Relevant code
`backend/migrations/001_init.sql`:

```sql
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename    TEXT NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    page_count  INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    char_count  BIGINT NOT NULL DEFAULT 0,
    file_size   BIGINT NOT NULL DEFAULT 0,
    sha256      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'processing',  -- processing | ready | failed
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_start  INTEGER,
    page_end    INTEGER,
    content     TEXT NOT NULL,
    embedding   vector(384) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
```

### What's happening
`documents.status` is the ingestion state machine (`processing` → `ready` | `failed`). `sha256` powers duplicate detection. Each chunk stores its text, the page span it came from (`page_start`/`page_end`, nullable when Docling lacks provenance), and a 384-float vector in pgvector's native `vector` type. The unique constraint makes chunk inserts idempotent.

### Why it matters
This schema is why the app needs no separate vector store: metadata, text, and vectors live together, so a document delete can never orphan vectors. The `status` column is what the frontend polls during ingestion.

---

## Byte 2 — The vector index

### Builds on
Byte 1 (schema).

### In plain terms
An `ivfflat` index with `vector_cosine_ops` accelerates approximate nearest-neighbor search by cosine similarity. Without it, every query would scan every chunk's 384 floats.

### Relevant code
```sql
-- Approximate nearest-neighbour index for cosine search.
-- lists = 100 is a sane default for corpora up to ~1M chunks; ANALYZE after bulk load.
CREATE INDEX IF NOT EXISTS chunks_embedding_ivfflat_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);
```

### What's happening
`ivfflat` partitions the vector space into 100 lists (clusters); a query checks the nearest lists instead of all rows — approximate, but orders of magnitude faster at scale. `vector_cosine_ops` tells Postgres the distance metric is cosine. The second index speeds the `document_id = ANY(...)` scope filter used by the Notebook.

### Why it matters
Cosine search over raw vectors is O(n·d); the index makes retrieval effectively constant-time for this corpus size. The comment documents the tuning rationale (`lists=100` for ≤1M chunks).

---

## Byte 3 — `search_chunks()`: the similarity query

### Builds on
Bytes 1–2.

### In plain terms
`db.search_chunks()` is the single SQL query behind every question. It embeds the cosine-distance operator (`<=>`), converts distance to similarity (`1 - distance`), joins chunk metadata with document titles, optionally restricts to selected documents, and returns the top-K most similar chunks from `ready` documents only.

### Relevant code
`backend/app/db.py`:

```python
def search_chunks(query_embedding, top_k, document_ids=None):
    q = _vec_literal(query_embedding)
    where = "WHERE d.status = 'ready'"
    params = [q]
    if document_ids:
        where += " AND c.document_id = ANY(%s::uuid[])"
        params.append(list(document_ids))
    params.extend([q, top_k])
    ...
    SELECT c.id, c.document_id, c.chunk_index, c.page_start, c.page_end,
           c.content,
           d.filename, d.title,
           1 - (c.embedding <=> %s::vector) AS similarity
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    {where}
    ORDER BY c.embedding <=> %s::vector
    LIMIT %s
```

### What's happening
pgvector's `<=>` is cosine *distance* (0 = identical); `1 - distance` gives the similarity score the rest of the system uses. The `WHERE d.status = 'ready'` clause excludes still-processing or failed documents. The `document_ids` filter (Notebook scope) is appended only when given — note the careful parameter ordering documented in the comment. Embeddings are passed as text literals (`[0.1,0.2,…]`) cast to `::vector`.

### Why it matters
This one query *is* semantic search in Vector-Brain. `retrieval.py` calls it with `top_k × 2` and then applies the score threshold in Python — the SQL does ranking, Python does filtering.

---

## Byte 4 — Pooling, migrations, and the no-SQL rule

### Builds on
Bytes 1–3.

### In plain terms
`db.py` wraps a `psycopg3` connection pool (1–10 connections, autocommit) and owns *all* SQL in the codebase — the API layer never writes SQL. Migrations run from `backend/migrations/*.sql` at startup, idempotently.

### Relevant code
```python
_pool = ConnectionPool(
    settings.DATABASE_URL, min_size=1, max_size=10,
    kwargs={"row_factory": dict_row, "autocommit": True},
)

def run_migrations() -> None:
    """Apply SQL migration files in order. Idempotent (IF NOT EXISTS everywhere)."""
    ...
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        cur.execute(path.read_text(encoding="utf-8"))
```

### What's happening
`dict_row` makes every query return dicts (so callers use `h["similarity"]`, not tuples). Autocommit keeps writes simple — each statement is its own transaction, which is fine because writes are small and independent. `run_migrations` executes migration files in sorted order; every DDL uses `IF NOT EXISTS`, so restarts are safe.

### Why it matters
Centralizing SQL in `db.py` means there's exactly one place to audit queries, and the API layer stays free of string-interpolated SQL (all parameters are bound via `%s` placeholders — no injection surface).

---

## Putting It Together

`001_init.sql` defines the world (two tables, one vector index); `db.py` is the only module that speaks SQL, exposing typed Python functions (`create_document`, `insert_chunks`, `search_chunks`, …) over a pooled, autocommitting connection. Ingestion writes through it, retrieval reads through it, and the cascade + status column keep the UI honest. Next: [Ingestion](./ingest.md) (how rows get created) and [Retrieval](./retrieval.md) (how rows get found).
