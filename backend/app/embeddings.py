"""
Vector-Brain backend — 384-dimensional text embeddings.

Production path: sentence-transformers `all-MiniLM-L6-v2` on CPU (384 dims,
matching the pgvector `vector(384)` column). The model is loaded lazily and
cached; on Apple Silicon we pin device="cpu" (the MPS backend has crashed on
local embedding loads in the past).

Mock path: deterministic hash-based unit vectors for tests — no model download,
no network. Never used in production unless MOCK_EMBEDDINGS=true is set.
"""

from __future__ import annotations

import hashlib
import math
import threading
from typing import Sequence

import numpy as np

from .config import get_settings

_model = None
# Serializes lazy model loading. SentenceTransformer/transformers builds the
# model on the torch "meta" device during from_pretrained; two threads doing
# that at once corrupt each other and one loader ends up with meta tensors
# ("Cannot copy out of meta tensor"). Seen live with 3 simultaneous uploads.
_model_lock = threading.Lock()


def _load_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked: only one thread loads
                from sentence_transformers import SentenceTransformer

                settings = get_settings()
                # Explicit CPU: avoids Metal/MPS crashes on Apple Silicon.
                _model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _model


def _mock_embed(texts: Sequence[str], dim: int) -> list[list[float]]:
    """
    Deterministic pseudo-embeddings: one binary hash bucket per token,
    L2-normalized. Related texts share tokens and therefore buckets, which is
    enough to exercise retrieval ranking in tests. (One bucket per token keeps
    the 384-dim space sparse so unrelated texts stay near-orthogonal.)
    """
    out: list[list[float]] = []
    for text in texts:
        buckets = set()
        for tok in text.lower().split():
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            buckets.add(h % dim)
        vec = [0.0] * dim
        for b in buckets:
            vec[b] = 1.0
        norm = math.sqrt(len(buckets)) or 1.0
        out.append([v / norm for v in vec])
    return out


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns L2-normalized 384-dim vectors."""
    settings = get_settings()
    if settings.MOCK_EMBEDDINGS:
        return _mock_embed(texts, settings.EMBEDDING_DIM)
    model = _load_model()
    arr = model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
    arr = np.asarray(arr, dtype=np.float32)
    if arr.shape[1] != settings.EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding dim mismatch: got {arr.shape[1]}, expected {settings.EMBEDDING_DIM}"
        )
    return arr.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1.0
    return float(np.dot(va, vb) / denom)
