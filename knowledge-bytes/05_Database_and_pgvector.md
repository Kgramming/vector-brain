# 05 — Database and pgvector

The two tables everything else reads and writes, and the index that makes semantic search fast.

Source files in this byte: `backend/migrations/001_init.sql`, `backend/app/db.py` (all SQL lives here — the API layer never touches SQL)

---

### Byte 1: Two tables, one cascade

**Builds on:** `01`

**In plain terms:**
`documents` is one row per PDF with a lifecycle status (`processing` → `ready` | `failed`); `chunks` is one row per text chunk with its 384-dim vector. `ON DELETE CASCADE` means deleting a document deletes its vectors — metadata and embeddings can never drift apart.

**The code:**
```sql
-- backend/migrations/001_init.sql
CREATE TABLE chunks (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_start  INTEGER,          -- nullable: Docling sometimes lacks provenance
    page_end    INTEGER,
    content     TEXT NOT NULL,
    embedding   vector(384) NOT NULL,
    UNIQUE (document_id, chunk_index)   -- inserts are idempotent
);
```

`documents` also carries `sha256` (duplicate detection), `page_count`/`chunk_count`/`char_count` (the Library UI), and `error` (why an ingestion failed).

---

### Byte 2: The vector index

**Builds on:** Byte 1

**In plain terms:**
An `ivfflat` index with `vector_cosine_ops` partitions the vector space into 100 lists so queries check nearby clusters instead of scanning every 384-float vector. Without it, every question would be a full table scan.

**The code:**
```sql
CREATE INDEX chunks_embedding_ivfflat_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX chunks_document_id_idx ON chunks (document_id);  -- for scope filtering
```

---

### Byte 3: All SQL lives in `db.py`

**Builds on:** Bytes 1–2

**In plain terms:**
`db.py` wraps a `psycopg3` pool (1–10 connections, autocommit, dict rows) and exposes typed Python functions — `create_document`, `insert_chunks`, `search_chunks`, `mark_document_ready/failed`, … — so the API layer never writes SQL and every parameter is bound (no injection surface). Migrations run from `backend/migrations/*.sql` at startup, idempotently.

**The code:**
```python
# backend/app/db.py
_pool = ConnectionPool(settings.DATABASE_URL, min_size=1, max_size=10,
                       kwargs={"row_factory": dict_row, "autocommit": True})

def run_migrations() -> None:
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):  # IF NOT EXISTS everywhere
        cur.execute(path.read_text(encoding="utf-8"))
```

---

## PUTTING IT TOGETHER

Two tables, one vector index, one module that owns all SQL. Ingestion writes through `db.py`, retrieval reads through it, and the cascade plus the `status` column keep the UI honest. There is no cache, no queue, no secondary store — if you can read these tables, you can see exactly what the system knows.
