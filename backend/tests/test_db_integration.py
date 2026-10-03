"""Integration tests against a REAL PostgreSQL + pgvector.

Run with:
    VECTORBRAIN_TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/vectorbrain_test \
        python -m pytest tests/test_db_integration.py -v

Skipped by default so the unit suite stays dependency-light.
"""

import os
import uuid

import pytest

from app import db
from app.config import get_settings

TEST_URL = os.environ.get("VECTORBRAIN_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not TEST_URL, reason="VECTORBRAIN_TEST_DATABASE_URL not set")


def _vec(seed: int) -> list[float]:
    # deterministic unit-ish vectors: mostly zeros with a spike pattern
    v = [0.0] * 384
    for i in range(8):
        v[(seed * 37 + i * 53) % 384] = 1.0
    n = sum(x * x for x in v) ** 0.5
    return [x / n for x in v]


@pytest.fixture()
def conn(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    get_settings.cache_clear()
    db.close_pool()
    db.run_migrations()
    yield
    # clean slate
    with db.cursor() as cur:
        cur.execute("TRUNCATE documents CASCADE")
    db.close_pool()
    get_settings.cache_clear()


@needs_db
def test_full_ingest_and_search_roundtrip(conn):
    doc = db.create_document("ml-notes.pdf", "ML Notes", 1234, "sha-" + uuid.uuid4().hex)
    assert doc["status"] == "processing"

    chunks = [
        {"chunk_index": 0, "page_start": 1, "page_end": 1,
         "content": "gradient descent optimizes neural networks", "embedding": _vec(1)},
        {"chunk_index": 1, "page_start": 2, "page_end": 2,
         "content": "photosynthesis occurs in chloroplasts", "embedding": _vec(2)},
        {"chunk_index": 2, "page_start": 3, "page_end": 3,
         "content": "backpropagation computes gradients efficiently", "embedding": _vec(3)},
    ]
    db.insert_chunks(str(doc["id"]), chunks)
    db.mark_document_ready(str(doc["id"]), 3, 3, 120)
    assert db.count_chunks() == 3

    # query close to chunk 0's vector -> chunk 0 must rank first
    hits = db.search_chunks(_vec(1), top_k=3)
    assert len(hits) == 3
    assert hits[0]["chunk_index"] == 0
    assert hits[0]["similarity"] > 0.99
    assert hits[0]["filename"] == "ml-notes.pdf"

    # processing documents are invisible to search
    doc2 = db.create_document("draft.pdf", "Draft", 10, "sha-" + uuid.uuid4().hex)
    db.insert_chunks(str(doc2["id"]), [
        {"chunk_index": 0, "page_start": 1, "page_end": 1, "content": "x", "embedding": _vec(1)},
    ])
    hits2 = db.search_chunks(_vec(1), top_k=10)
    assert all(h["document_id"] != doc2["id"] for h in hits2)


@needs_db
def test_delete_cascades_chunks(conn):
    doc = db.create_document("t.pdf", "T", 1, "sha-" + uuid.uuid4().hex)
    db.insert_chunks(str(doc["id"]), [
        {"chunk_index": 0, "page_start": 1, "page_end": 1, "content": "x", "embedding": _vec(5)},
    ])
    assert db.delete_document(str(doc["id"])) is True
    assert db.count_chunks() == 0
    assert db.delete_document(str(doc["id"])) is False


@needs_db
def test_vector_dimension_enforced(conn):
    doc = db.create_document("t.pdf", "T", 1, "sha-" + uuid.uuid4().hex)
    with pytest.raises(Exception):
        db.insert_chunks(str(doc["id"]), [
            {"chunk_index": 0, "page_start": 1, "page_end": 1,
             "content": "x", "embedding": [0.1] * 128},  # wrong dim
        ])


@needs_db
def test_search_chunks_document_ids_filter_real_pgvector(conn):
    """Real pgvector binding: vector literal -> ::vector, ids -> ::uuid[].

    Regression test for the InvalidTextRepresentation crash
    ("malformed array literal ... Missing ] after array dimensions")
    caused by misordered positional params when document_ids was used.
    """
    def make_doc(name, seed):
        doc = db.create_document(name, name, 100, "sha-" + uuid.uuid4().hex)
        db.insert_chunks(str(doc["id"]), [
            {"chunk_index": 0, "page_start": 1, "page_end": 1,
             "content": f"content of {name}", "embedding": _vec(seed)},
        ])
        db.mark_document_ready(str(doc["id"]), 1, 1, 20)
        return doc

    doc_a = make_doc("a.pdf", 11)
    doc_b = make_doc("b.pdf", 22)

    # unfiltered: both documents searchable
    hits_all = db.search_chunks(_vec(11), top_k=10)
    assert {h["document_id"] for h in hits_all} == {doc_a["id"], doc_b["id"]}

    # filtered: only doc_b's chunks, even though the query is closest to doc_a
    hits_b = db.search_chunks(_vec(11), top_k=10, document_ids=[str(doc_b["id"])])
    assert len(hits_b) == 1
    assert hits_b[0]["document_id"] == doc_b["id"]
    assert hits_b[0]["filename"] == "b.pdf"

    # multiple ids
    hits_ab = db.search_chunks(
        _vec(11), top_k=10, document_ids=[str(doc_a["id"]), str(doc_b["id"])])
    assert {h["document_id"] for h in hits_ab} == {doc_a["id"], doc_b["id"]}
