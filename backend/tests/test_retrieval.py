"""Unit tests for retrieval helpers and the Knowledge Bytes module."""

from app import retrieval
from app.knowledge_bytes import build_knowledge_bytes_prompt, render_bytes_preview
from app.retrieval import format_context


def _hit(i, sim=0.8):
    return {
        "id": f"c{i}", "document_id": f"d{i}", "chunk_index": i,
        "page_start": i + 1, "page_end": i + 1, "content": f"chunk content {i}",
        "filename": f"notes{i}.pdf", "title": f"Notes {i}", "similarity": sim,
    }


def test_format_context_numbers_citations():
    ctx = format_context([_hit(0), _hit(1)])
    assert ctx.startswith("[1] Notes 0")
    assert "[2] Notes 1" in ctx
    assert "chunk content 0" in ctx


def test_format_context_empty():
    assert format_context([]) == ""


def test_retrieve_threshold_filters(monkeypatch):
    # fake DB hits: one above threshold, one below
    monkeypatch.setattr(
        retrieval.db, "search_chunks",
        lambda qvec, k, doc_ids=None: [_hit(0, sim=0.9), _hit(1, sim=0.05)],
    )
    hits = retrieval.retrieve("anything about vectors")
    assert len(hits) == 1
    assert hits[0]["similarity"] == 0.9


def test_retrieve_respects_top_k(monkeypatch):
    monkeypatch.setattr(
        retrieval.db, "search_chunks",
        lambda qvec, k, doc_ids=None: [_hit(i, sim=0.9 - i * 0.01) for i in range(10)],
    )
    hits = retrieval.retrieve("q", top_k=3)
    assert len(hits) == 3


def test_retrieve_passes_document_ids(monkeypatch):
    seen = {}

    def fake_search(qvec, k, doc_ids=None):
        seen["doc_ids"] = doc_ids
        return [_hit(0, sim=0.9)]

    monkeypatch.setattr(retrieval.db, "search_chunks", fake_search)
    hits = retrieval.retrieve("q", document_ids=["d0"])
    assert len(hits) == 1
    assert seen["doc_ids"] == ["d0"]


def test_retrieve_document_ids_default_none(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        retrieval.db, "search_chunks",
        lambda qvec, k, doc_ids=None: seen.update(doc_ids=doc_ids) or [_hit(0, sim=0.9)],
    )
    retrieval.retrieve("q")
    assert seen["doc_ids"] is None


def test_knowledge_bytes_prompt_has_architecture_first_format():
    msgs = build_knowledge_bytes_prompt("def f():\n    pass", language="python")
    system = msgs[0]["content"]
    for section in ["BYTE N", "ROLE:", "FLOW:", "CONNECTS TO:", "WHY:", "KEY CODE:", "PUTTING IT TOGETHER"]:
        assert section in system
    assert "10 seconds" in system
    assert "```" in msgs[1]["content"]
    assert "python" in msgs[1]["content"].lower()


def test_knowledge_bytes_prompt_truncates_huge_content():
    msgs = build_knowledge_bytes_prompt("x" * 100000)
    assert len(msgs[1]["content"]) < 30000


def test_knowledge_bytes_preview_skeleton():
    preview = render_bytes_preview("def ingest():\n    pass")
    assert "BYTE 1" in preview
    assert "PUTTING IT TOGETHER" in preview
