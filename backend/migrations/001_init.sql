-- Vector-Brain migration 001: initial schema
-- PostgreSQL + pgvector. Embedding dimension is 384 (all-MiniLM-L6-v2).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE IF NOT EXISTS documents (
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

CREATE TABLE IF NOT EXISTS chunks (
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

-- Approximate nearest-neighbour index for cosine search.
-- lists = 100 is a sane default for corpora up to ~1M chunks; ANALYZE after bulk load.
CREATE INDEX IF NOT EXISTS chunks_embedding_ivfflat_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);
