"""
Vector-Brain backend — semantic retrieval over pgvector.

One function owns the whole retrieve step: embed the question, run the cosine
ANN query across ALL documents, keep only hits above SCORE_THRESHOLD.
"""

from __future__ import annotations

from . import db
from .config import get_settings
from .embeddings import embed_query


def retrieve(question: str, top_k: int | None = None) -> list[dict]:
    settings = get_settings()
    top_k = top_k or settings.TOP_K
    qvec = embed_query(question)
    hits = db.search_chunks(qvec, top_k * 2)  # over-fetch, then threshold
    kept = [h for h in hits if h["similarity"] >= settings.SCORE_THRESHOLD]
    return kept[:top_k]


def format_context(hits: list[dict]) -> str:
    """Numbered context block injected into the chat prompt; numbers are the citations."""
    parts = []
    for i, h in enumerate(hits, start=1):
        label = h["title"] or h["filename"]
        page = f", p.{h['page_start']}" if h.get("page_start") else ""
        parts.append(f"[{i}] {label}{page}:\n{h['content']}")
    return "\n\n".join(parts)
