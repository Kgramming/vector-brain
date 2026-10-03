"""
Vector-Brain backend — database access.

Thin wrapper around a psycopg3 connection pool. All SQL lives here so the
API layer never touches SQL directly. Schema is defined in
backend/migrations/001_init.sql and applied on startup (idempotent).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import get_settings

_pool: ConnectionPool | None = None
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        # autocommit=True: each statement is its own transaction; the API
        # layer keeps writes small and independent, so this keeps the code
        # simple without a unit-of-work abstraction. (Passed via kwargs:
        # psycopg_pool forwards them to each new connection.)
        _pool = ConnectionPool(
            settings.DATABASE_URL, min_size=1, max_size=10,
            kwargs={"row_factory": dict_row, "autocommit": True},
        )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def run_migrations() -> None:
    """Apply SQL migration files in order. Idempotent (IF NOT EXISTS everywhere)."""
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                cur.execute(path.read_text(encoding="utf-8"))


@contextmanager
def cursor() -> Iterator[Any]:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            yield cur


# ---------------------------------------------------------------- documents

def create_document(filename: str, title: str, file_size: int, sha256: str) -> dict:
    with cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (filename, title, file_size, sha256, status)
            VALUES (%s, %s, %s, %s, 'processing')
            RETURNING id, filename, title, status, created_at
            """,
            (filename, title, file_size, sha256),
        )
        return cur.fetchone()


def mark_document_ready(doc_id: str, page_count: int, chunk_count: int, char_count: int) -> None:
    with cursor() as cur:
        cur.execute(
            """
            UPDATE documents
            SET status='ready', page_count=%s, chunk_count=%s, char_count=%s, error=NULL
            WHERE id=%s
            """,
            (page_count, chunk_count, char_count, doc_id),
        )


def mark_document_failed(doc_id: str, error: str) -> None:
    with cursor() as cur:
        cur.execute(
            "UPDATE documents SET status='failed', error=%s WHERE id=%s",
            (error[:2000], doc_id),
        )


def list_documents() -> list[dict]:
    with cursor() as cur:
        cur.execute(
            """
            SELECT id, filename, title, page_count, chunk_count, char_count,
                   file_size, status, error, created_at
            FROM documents ORDER BY created_at DESC
            """
        )
        return cur.fetchall()


def delete_document(doc_id: str) -> bool:
    with cursor() as cur:
        cur.execute("DELETE FROM documents WHERE id=%s", (doc_id,))
        return cur.rowcount > 0


def document_exists(doc_id: str) -> bool:
    with cursor() as cur:
        cur.execute("SELECT 1 FROM documents WHERE id=%s", (doc_id,))
        return cur.fetchone() is not None


# ---------------------------------------------------------------- chunks

def _vec_literal(vec: Sequence[float]) -> str:
    """Render an embedding as a pgvector text literal: '[0.1, 0.2, ...]'."""
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def insert_chunks(doc_id: str, chunks: Sequence[dict]) -> None:
    """chunks: list of {chunk_index, page_start, page_end, content, embedding}."""
    if not chunks:
        return
    rows = [
        (doc_id, c["chunk_index"], c.get("page_start"), c.get("page_end"),
         c["content"], _vec_literal(c["embedding"]))
        for c in chunks
    ]
    with cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (document_id, chunk_index, page_start, page_end, content, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id, chunk_index) DO NOTHING
            """,
            rows,
        )


def search_chunks(query_embedding: Sequence[float], top_k: int) -> list[dict]:
    """
    Cosine-similarity search across ALL documents.
    pgvector's <=> is cosine distance; similarity = 1 - distance.
    """
    q = _vec_literal(query_embedding)
    with cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.document_id, c.chunk_index, c.page_start, c.page_end,
                   c.content,
                   d.filename, d.title,
                   1 - (c.embedding <=> %s::vector) AS similarity
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.status = 'ready'
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
            """,
            (q, q, top_k),
        )
        return cur.fetchall()


def count_chunks() -> int:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM chunks")
        return cur.fetchone()["n"]
