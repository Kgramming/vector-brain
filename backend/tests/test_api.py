"""API tests with the database layer faked out (no PostgreSQL needed).

Covers: health, upload validation, chat sync incl. citation suppression on
refusal, and the Knowledge Bytes mock stream. Lifespan migrations are stubbed.
"""

import io
import json

import pytest
from fastapi.testclient import TestClient

from app import db as db_module
from app.api import routes as routes_module
from app.main import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(db_module, "run_migrations", lambda: None)
    monkeypatch.setattr(db_module, "close_pool", lambda: None)
    app = create_app()
    with TestClient(app) as c:
        yield c


def _sse_sources(resp):
    """Return the parsed `sources` event payload, or None if absent."""
    for chunk in resp.text.split("\n\n"):
        lines = chunk.splitlines()
        if lines and lines[0].strip() == "event: sources":
            for line in lines[1:]:
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())["sources"]
    return None


def _sse_text(resp):
    """Collect all `token` payloads from an SSE response body."""
    out = []
    for chunk in resp.text.split("\n\n"):
        for line in chunk.splitlines():
            if line.startswith("data:"):
                try:
                    payload = json.loads(line[5:].strip())
                except ValueError:
                    continue
                if "token" in payload:
                    out.append(payload["token"])
    return "".join(out)


def test_health_degraded_without_db(client, monkeypatch):
    monkeypatch.setattr(db_module, "list_documents", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "degraded"
    assert body["groq_mode"] == "mock"


def test_health_ok(client, monkeypatch):
    monkeypatch.setattr(db_module, "list_documents", lambda: [])
    monkeypatch.setattr(db_module, "count_chunks", lambda: 0)
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["documents"] == 0


def test_upload_rejects_non_pdf(client):
    res = client.post("/api/documents", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code == 400


def test_upload_rejects_empty_pdf(client):
    res = client.post("/api/documents", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert res.status_code == 400


def test_upload_rejects_oversized_pdf(client, monkeypatch):
    # shrink the limit via the settings instance used by the route
    monkeypatch.setattr(type(routes_module.settings), "max_upload_bytes", property(lambda self: 10))
    res = client.post("/api/documents", files={"file": ("big.pdf", b"x" * 11, "application/pdf")})
    assert res.status_code == 413


def test_upload_rejects_duplicate_pdf(client, monkeypatch, tmp_path):
    data = b"%PDF-1.4 fake"
    monkeypatch.setattr(db_module, "list_documents", lambda: [{"sha256": "abc", "status": "ready"}])
    import hashlib
    monkeypatch.setattr(
        db_module, "list_documents",
        lambda: [{"sha256": hashlib.sha256(data).hexdigest(), "status": "ready"}],
    )
    res = client.post("/api/documents", files={"file": ("dup.pdf", data, "application/pdf")})
    assert res.status_code == 409


def test_chat_sync_attaches_sources(client, monkeypatch):
    hits = [{
        "document_id": "d1", "filename": "notes.pdf", "title": "Notes",
        "chunk_index": 0, "page_start": 2, "page_end": 2,
        "content": "photosynthesis happens in chloroplasts", "similarity": 0.85,
    }]
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: hits)
    res = client.post("/api/chat/sync", json={"question": "Where does photosynthesis happen?"})
    assert res.status_code == 200
    body = res.json()
    assert body["declined"] is False
    assert len(body["sources"]) == 1
    assert body["sources"][0]["title"] == "Notes"
    assert body["sources"][0]["page_start"] == 2


def test_chat_sync_no_hits_declines_without_sources(client, monkeypatch):
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: [])
    body = client.post("/api/chat/sync", json={"question": "unrelated?"}).json()
    assert body["declined"] is True
    assert body["sources"] == []


def test_chat_sync_forwards_document_ids(client, monkeypatch):
    seen = {}

    def fake_retrieve(q, top_k=None, document_ids=None):
        seen["document_ids"] = document_ids
        return []

    monkeypatch.setattr(routes_module, "retrieve", fake_retrieve)
    body = client.post(
        "/api/chat/sync",
        json={"question": "q?", "document_ids": ["d1", "d2"]},
    ).json()
    assert body["declined"] is True  # no hits -> decline path
    assert seen["document_ids"] == ["d1", "d2"]


def test_chat_sync_document_ids_optional(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        routes_module, "retrieve",
        lambda q, top_k=None, document_ids=None: seen.update(ids=document_ids) or [],
    )
    client.post("/api/chat/sync", json={"question": "q?"})
    assert seen["ids"] is None


def test_chat_sync_refusal_suppresses_sources(client, monkeypatch):
    hits = [{
        "document_id": "d1", "filename": "n.pdf", "title": "N",
        "chunk_index": 0, "page_start": 1, "page_end": 1,
        "content": "something", "similarity": 0.9,
    }]
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: hits)
    monkeypatch.setattr(routes_module, "chat_once", lambda q, ctx: "[DECLINED] not in context")
    body = client.post("/api/chat/sync", json={"question": "q"}).json()
    assert body["declined"] is True
    assert body["sources"] == []  # citations suppressed on refusal
    assert "[DECLINED]" not in body["answer"]


def test_chat_stream_emits_sources_then_done(client, monkeypatch):
    hits = [{
        "document_id": "d1", "filename": "n.pdf", "title": "N",
        "chunk_index": 0, "page_start": 1, "page_end": 1,
        "content": "c", "similarity": 0.9,
    }]
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: hits)
    res = client.post("/api/chat", json={"question": "q"})
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert "event: sources" in res.text
    assert "event: done" in res.text
    assert len(_sse_text(res)) > 0


def test_chat_stream_refusal_suppresses_sources(client, monkeypatch):
    """A model-level refusal (hits retrieved, LLM emits [DECLINED]) must not
    leak citations over SSE: the sources event carries an empty list,
    matching /chat/sync. Regression: sources used to be emitted before the
    marker decision was known."""
    hits = [{
        "document_id": "d1", "filename": "n.pdf", "title": "N",
        "chunk_index": 0, "page_start": 1, "page_end": 1,
        "content": "c", "similarity": 0.9,
    }]
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: hits)
    # chunk the marker across tokens to prove prefix detection still works
    monkeypatch.setattr(
        routes_module, "stream_chat",
        lambda q, ctx: iter(["[DECL", "INED] not in the provided context"]),
    )
    res = client.post("/api/chat", json={"question": "q"})
    assert res.status_code == 200
    assert _sse_sources(res) == []
    text = _sse_text(res)
    assert "[DECLINED]" not in text
    assert "not in the provided context" in text
    assert '"declined": true' in res.text


def test_chat_stream_normal_answer_carries_sources(client, monkeypatch):
    hits = [{
        "document_id": "d1", "filename": "n.pdf", "title": "N",
        "chunk_index": 0, "page_start": 1, "page_end": 1,
        "content": "c", "similarity": 0.9,
    }]
    monkeypatch.setattr(routes_module, "retrieve", lambda q, top_k=None, document_ids=None: hits)
    monkeypatch.setattr(
        routes_module, "stream_chat",
        lambda q, ctx: iter(["Photosynthesis happens in chloroplasts [1]."]),
    )
    res = client.post("/api/chat", json={"question": "q"})
    assert res.status_code == 200
    srcs = _sse_sources(res)
    assert srcs and srcs[0]["filename"] == "n.pdf"
    assert '"declined": false' in res.text


def test_knowledge_bytes_mock_streams_skeleton(client):
    res = client.post("/api/knowledge-bytes", json={"content": "def f():\n    pass"})
    assert res.status_code == 200
    text = _sse_text(res)
    assert "BYTE 1" in text
    assert "PUTTING IT TOGETHER" in text


def test_knowledge_bytes_rejects_empty(client):
    res = client.post("/api/knowledge-bytes", json={"content": "  "})
    assert res.status_code == 422
