"""Unit tests for the ingestion pipeline orchestration (DB faked)."""

from app import pipeline as pipeline_module
from app.ingest import ParsedDocument, TextItem


def _parsed():
    return ParsedDocument(
        title="T",
        page_count=2,
        items=[TextItem(text="alpha beta gamma", page_no=1), TextItem(text="delta epsilon", page_no=2)],
    )


def test_process_upload_happy_path(monkeypatch, tmp_path):
    calls = {}

    def fake_ingest(path, extractor=None):
        parsed = _parsed()
        from app.ingest import chunk_items
        return parsed, chunk_items(parsed.items, chunk_size=50, chunk_overlap=10)

    monkeypatch.setattr(pipeline_module, "ingest_pdf", fake_ingest)
    monkeypatch.setattr(pipeline_module, "embed_texts", lambda texts: [[0.1] * 384 for _ in texts])
    monkeypatch.setattr(pipeline_module.db, "insert_chunks", lambda doc_id, chunks: calls.update(inserted=chunks))
    monkeypatch.setattr(
        pipeline_module.db, "mark_document_ready",
        lambda doc_id, pages, n_chunks, chars: calls.update(ready=(doc_id, pages, n_chunks, chars)),
    )
    monkeypatch.setattr(pipeline_module.db, "mark_document_failed", lambda *a: calls.update(failed=a))

    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF fake")
    pipeline_module.process_upload("doc-1", str(f))

    assert "failed" not in calls
    assert calls["ready"][0] == "doc-1"
    assert calls["ready"][1] == 2  # page_count
    assert len(calls["inserted"]) == calls["ready"][2] > 0
    assert all(len(c["embedding"]) == 384 for c in calls["inserted"])
    assert not f.exists()  # temp file cleaned up


def test_process_upload_marks_failed_and_cleans_up(monkeypatch, tmp_path):
    calls = {}

    def boom(path, extractor=None):
        raise ValueError("no text")

    monkeypatch.setattr(pipeline_module, "ingest_pdf", boom)
    monkeypatch.setattr(pipeline_module.db, "mark_document_failed", lambda doc_id, err: calls.update(err=err))

    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF fake")
    pipeline_module.process_upload("doc-9", str(f))

    assert "ValueError" in calls["err"]
    assert not f.exists()
