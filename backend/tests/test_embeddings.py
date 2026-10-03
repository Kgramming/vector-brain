"""Unit tests for embeddings in MOCK mode (deterministic, no download)."""

import math

from app.config import get_settings
from app.embeddings import cosine_similarity, embed_query, embed_texts


def test_mock_embeddings_are_384_dim():
    vecs = embed_texts(["hello world", "another text"])
    assert len(vecs) == 2
    assert all(len(v) == get_settings().EMBEDDING_DIM == 384 for v in vecs)


def test_mock_embeddings_are_normalized():
    for v in embed_texts(["some study notes about photosynthesis"]):
        assert math.isclose(sum(x * x for x in v), 1.0, rel_tol=1e-6)


def test_mock_embeddings_are_deterministic():
    a = embed_texts(["repeat me"])
    b = embed_texts(["repeat me"])
    assert a == b


def test_similar_texts_score_higher():
    q = embed_query("vector database indexing")
    related = embed_query("vector database indexing techniques")
    unrelated = embed_query("medieval poetry about falcons")
    assert cosine_similarity(q, related) > cosine_similarity(q, unrelated)


def test_cosine_similarity_known_values():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9
