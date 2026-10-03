"""
Vector-Brain backend — ingestion pipeline.

Owns the full upload lifecycle: parse (Docling) -> chunk -> embed (384-dim)
-> store (pgvector) -> mark ready. Runs as a FastAPI BackgroundTask so the
upload endpoint returns immediately; the frontend polls document status.
"""

from __future__ import annotations

import logging
import os

from . import db
from .embeddings import embed_texts
from .ingest import ingest_pdf

log = logging.getLogger("vectorbrain.pipeline")


def process_upload(doc_id: str, saved_path: str) -> None:
    try:
        parsed, chunks = ingest_pdf(saved_path)
        log.info("Parsed %s: %d items -> %d chunks", saved_path, len(parsed.items), len(chunks))

        # Batch-embed chunk contents, then attach vectors.
        vectors = embed_texts([c["content"] for c in chunks])
        for chunk, vec in zip(chunks, vectors):
            chunk["embedding"] = vec

        db.insert_chunks(doc_id, chunks)
        char_count = sum(len(c["content"]) for c in chunks)
        db.mark_document_ready(doc_id, parsed.page_count, len(chunks), char_count)
        log.info("Document %s ready: %d chunks", doc_id, len(chunks))
    except Exception as exc:  # noqa: BLE001 - must never crash the worker silently
        log.exception("Ingestion failed for document %s", doc_id)
        db.mark_document_failed(doc_id, f"{type(exc).__name__}: {exc}")
    finally:
        try:
            os.remove(saved_path)
        except OSError:
            pass
