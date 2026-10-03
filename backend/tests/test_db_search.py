"""Unit tests for db.search_chunks parameter binding.

Regression coverage for the positional-parameter ordering bug where the
384-dim vector literal was bound to the %s::uuid[] placeholder (and the id
list to %s::vector), producing:
    psycopg.errors.InvalidTextRepresentation: malformed array literal
whenever document_ids filtering was used.

These tests capture the SQL + params via a fake cursor — no DB needed.
"""

import re

import pytest

from app import db


class FakeCursor:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, list(params or [])))

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture()
def capture(monkeypatch):
    fake = FakeCursor()
    monkeypatch.setattr(db, "cursor", lambda: fake)
    return fake


def _casts_in_order(query):
    """Return the type cast of each %s placeholder, in positional order."""
    return [c or None for c in re.findall(r"%s(?:::(\w+\[\]|vector))?", query)]


def test_search_chunks_param_order_with_document_ids(capture):
    vec = [0.5] * 384
    doc_id = "12345678-1234-5678-1234-567812345678"
    db.search_chunks(vec, top_k=5, document_ids=[doc_id])

    assert len(capture.queries) == 1
    query, params = capture.queries[0]
    casts = _casts_in_order(query)

    # placeholders must appear as: vector, uuid[], vector, LIMIT
    assert casts == ["vector", "uuid[]", "vector", None], casts
    assert len(params) == 4

    # each param's shape must match its placeholder's cast
    assert params[0].startswith("[") and params[0].endswith("]")  # vector literal
    assert "0.500000" in params[0]
    assert params[1] == [doc_id]  # id list -> uuid[]
    assert params[2] == params[0]  # same vector literal for ORDER BY
    assert params[3] == 5  # LIMIT


def test_search_chunks_param_order_without_document_ids(capture):
    vec = [0.1] * 384
    db.search_chunks(vec, top_k=3)

    assert len(capture.queries) == 1
    query, params = capture.queries[0]
    casts = _casts_in_order(query)

    assert casts == ["vector", "vector", None], casts
    assert len(params) == 3
    assert params[0].startswith("[") and params[0].endswith("]")
    assert params[1] == params[0]
    assert params[2] == 3


def test_search_chunks_vector_literal_format(capture):
    # 384 dims, 6-decimal floats, bracketed — pgvector text input format
    db.search_chunks([0.123456789] * 384, top_k=1)
    _, params = capture.queries[0]
    inner = params[0][1:-1]
    parts = inner.split(",")
    assert len(parts) == 384
    assert parts[0] == "0.123457"
