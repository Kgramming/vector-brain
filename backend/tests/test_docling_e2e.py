"""REAL end-to-end ingestion test with the actual Docling library — no mocks.

Run with:
    RUN_REAL_E2E=1 VECTORBRAIN_TEST_DATABASE_URL=postgresql://... \
        python -m pytest tests/test_docling_e2e.py -v

Requires docling + sentence-transformers installed (heavy) and a real
PostgreSQL + pgvector. Skipped by default so the normal suite stays fast
and offline.

Verifies the true production path:
    real PDF -> Docling -> page-aware chunks -> real 384-dim MiniLM
    embeddings -> pgvector -> semantic retrieval -> chat citations -> delete.

The LLM *text* uses mock mode unless GROQ_API_KEY is set (clearly labeled);
everything else — parsing, chunking, embeddings, storage, retrieval,
citation attachment — is 100% real. This test FAILS if any mock is involved
in those stages (it asserts MOCK_EMBEDDINGS=false and a real
SentenceTransformer instance).
"""

import importlib.util
import os
import textwrap
import threading
import time
import uuid

import pytest

REAL_E2E = os.environ.get("RUN_REAL_E2E") == "1"
HAS_DOCLING = importlib.util.find_spec("docling") is not None
HAS_ST = importlib.util.find_spec("sentence_transformers") is not None
TEST_URL = os.environ.get("VECTORBRAIN_TEST_DATABASE_URL")

needs_real = pytest.mark.skipif(
    not (REAL_E2E and HAS_DOCLING and HAS_ST and TEST_URL),
    reason="needs RUN_REAL_E2E=1, docling, sentence-transformers, VECTORBRAIN_TEST_DATABASE_URL",
)


def make_pdf(path, title, pages):
    """Generate a small real multi-page PDF with reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    for i, paras in enumerate(pages):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 750, f"{title} — page {i + 1}")
        c.setFont("Helvetica", 11)
        y = 720
        for para in paras:
            for line in textwrap.wrap(para, 90):
                c.drawString(72, y, line)
                y -= 14
                if y < 60:
                    c.showPage()
                    y = 750
            y -= 10
        c.showPage()
    c.save()


DOC_A = (
    "photosynthesis-notes.pdf",
    "Photosynthesis Study Notes",
    [
        ["Chlorophyll absorbs red and blue light most efficiently, reflecting green. "
         "The Calvin cycle fixes carbon dioxide into sugar in the stroma of the chloroplast."],
        ["Light-dependent reactions occur in the thylakoid membranes. "
         "Water molecules are split, releasing oxygen as a byproduct of photosynthesis."],
    ],
)
DOC_B = (
    "cell-energy-notes.pdf",
    "Cellular Respiration Notes",
    [
        ["Mitochondria produce ATP through oxidative phosphorylation. "
         "ATP synthase spins like a tiny rotary motor embedded in the inner membrane."],
        ["Glycolysis breaks one glucose molecule into two pyruvate molecules in the cytoplasm, "
         "yielding a net gain of two ATP."],
    ],
)


@pytest.fixture()
def real_stack(monkeypatch, tmp_path):
    from app import db
    from app.config import get_settings

    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    monkeypatch.setenv("MOCK_EMBEDDINGS", "false")  # REAL embeddings
    get_settings.cache_clear()
    db.close_pool()
    db.run_migrations()
    with db.cursor() as cur:
        cur.execute("TRUNCATE documents CASCADE")
    yield tmp_path
    db.close_pool()
    get_settings.cache_clear()  # env restored by monkeypatch afterwards


def _wait_ready(client, doc_id, timeout=900):
    """Poll until the background Docling ingestion finishes."""
    start = time.time()
    while time.time() - start < timeout:
        docs = client.get("/api/documents").json()["documents"]
        match = [d for d in docs if d["id"] == doc_id]
        assert match, "uploaded document vanished"
        st = match[0]["status"]
        if st == "ready":
            return match[0]
        if st == "failed":
            pytest.fail(f"real ingestion failed: {match[0]['error']}")
        time.sleep(5)
    pytest.fail(f"ingestion of {doc_id} not ready after {timeout}s")


needs_real_model = pytest.mark.skipif(
    not (REAL_E2E and HAS_ST),
    reason="needs RUN_REAL_E2E=1 and sentence-transformers",
)


@needs_real_model
def test_concurrent_embedding_model_load(monkeypatch):
    """Regression: threads racing the lazy ST load must not corrupt each other.

    Found live 2026-10-04: three simultaneous uploads each triggered
    _load_model() at once; transformers builds the model on the torch "meta"
    device during from_pretrained, the concurrent inits raced, and one
    thread died with "Cannot copy out of meta tensor". _load_model() now
    serializes the load with a lock (double-checked).
    """
    from app import embeddings as emb_mod
    from app.config import get_settings

    monkeypatch.setenv("MOCK_EMBEDDINGS", "false")
    get_settings.cache_clear()
    assert get_settings().MOCK_EMBEDDINGS is False

    emb_mod._model = None  # force the lazy-load race
    errors: list = []
    results: list = []

    def worker(i):
        try:
            vecs = emb_mod.embed_texts([f"concurrency regression probe {i}"])
            assert len(vecs[0]) == 384
            results.append(vecs[0][:4])
        except Exception as e:  # noqa: BLE001 - collecting, asserted below
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=600)

    assert not errors, f"concurrent model load failed: {errors[0]!r}"
    assert len(results) == 3
    assert type(emb_mod._model).__name__ == "SentenceTransformer"
    get_settings.cache_clear()


@needs_real
def test_real_docling_end_to_end(real_stack, tmp_path):
    import os as _os

    from fastapi.testclient import TestClient

    from app import db
    from app.config import get_settings
    from app.main import create_app

    # --- 0. prove no mocks are in play ---
    assert _os.environ["MOCK_EMBEDDINGS"] == "false"
    assert get_settings().MOCK_EMBEDDINGS is False

    pdfs = {}
    for filename, title, pages in (DOC_A, DOC_B):
        p = tmp_path / filename
        make_pdf(p, title, pages)
        pdfs[filename] = p.read_bytes()
        assert len(pdfs[filename]) > 1000  # a real, non-trivial PDF

    with TestClient(create_app()) as client:
        # --- 1+2. upload accepted; Docling parses in the background ---
        ids = {}
        for filename, data in pdfs.items():
            r = client.post(
                "/api/documents",
                files={"file": (filename, data, "application/pdf")},
            )
            assert r.status_code == 202, r.text
            ids[filename] = r.json()["id"]

        doc_a = _wait_ready(client, ids[DOC_A[0]])
        doc_b = _wait_ready(client, ids[DOC_B[0]])

        # --- 3+4. extracted text non-empty, page info preserved ---
        assert doc_a["chunk_count"] > 0 and doc_a["char_count"] > 200
        assert doc_a["page_count"] >= 2, f"expected 2 pages, got {doc_a['page_count']}"

        with db.cursor() as cur:
            cur.execute(
                "SELECT page_start, page_end, content FROM chunks WHERE document_id=%s",
                (doc_a["id"],),
            )
            rows = cur.fetchall()
        assert rows, "no chunks stored"
        assert any(r["page_start"] is not None for r in rows), "page info lost"
        assert any("Chlorophyll" in r["content"] for r in rows), "PDF text not extracted"

        # --- 5+6+7. real 384-dim embeddings stored in pgvector ---
        from app import embeddings as emb_mod

        assert isinstance(emb_mod._model, object) and type(emb_mod._model).__name__ == "SentenceTransformer", \
            "embedding model is not the real SentenceTransformer"
        with db.cursor() as cur:
            cur.execute(
                "SELECT vector_dims(embedding) AS d, embedding <=> embedding AS dist "
                "FROM chunks WHERE document_id=%s LIMIT 1",
                (doc_a["id"],),
            )
            chk = cur.fetchone()
        assert chk["d"] == 384, f"expected vector(384), got vector({chk['d']})"
        assert abs(chk["dist"]) < 1e-6

        # --- 8. pgvector retrieval returns the relevant chunk ---
        q = emb_mod.embed_query("What absorbs red and blue light?")
        assert len(q) == 384
        hits = db.search_chunks(q, top_k=5)
        assert hits, "no retrieval hits"
        top = hits[0]
        assert "Chlorophyll" in top["content"], f"wrong top hit: {top['content'][:80]}"
        assert top["similarity"] > 0.3

        # --- cross-document retrieval: one query, both documents cited ---
        r = client.post(
            "/api/chat/sync",
            json={"question": "Where does photosynthesis happen and what produces ATP?", "top_k": 6},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["declined"] is False, body
        filenames = {s["filename"] for s in body["sources"]}
        assert DOC_A[0] in filenames and DOC_B[0] in filenames, filenames

        # --- 9. citation attached to the real document/page ---
        r = client.post("/api/chat/sync", json={"question": "What absorbs red and blue light?"})
        body = r.json()
        assert body["declined"] is False
        assert body["sources"], "answer has no citations"
        src = body["sources"][0]
        assert src["filename"] == DOC_A[0]
        assert src["page_start"] in (1, 2)
        assert "chlorophyll" in src["excerpt"].lower()
        assert 0 < src["similarity"] <= 1.0

        # --- streaming chat carries real sources over SSE ---
        with client.stream("POST", "/api/chat", json={"question": "What is ATP synthase?"}) as s:
            sse = s.read().decode()
        assert "event: sources" in sse and DOC_B[0] in sse
        assert "event: done" in sse and '"declined": false' in sse

        # --- 10. deletion removes chunks/vectors ---
        n_before = db.count_chunks()
        assert n_before >= 2
        dr = client.delete(f"/api/documents/{doc_a['id']}")
        assert dr.status_code == 200
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM chunks WHERE document_id=%s", (doc_a["id"],))
            assert cur.fetchone()["n"] == 0, "chunks survived document deletion"
        assert db.count_chunks() == n_before - doc_a["chunk_count"]
        # doc B untouched
        remaining = client.get("/api/documents").json()["documents"]
        assert any(d["id"] == doc_b["id"] for d in remaining)


@needs_real
def test_real_ingest_pdf_directly(real_stack, tmp_path):
    """Direct unit-level proof: ingest_pdf() with NO extractor override uses Docling."""
    from app.ingest import chunk_items, ingest_pdf

    p = tmp_path / "direct.pdf"
    make_pdf(p, "Direct Test", DOC_A[2])
    parsed, chunks = ingest_pdf(str(p))  # extractor=None -> real Docling path

    assert parsed.items, "Docling extracted nothing"
    assert len(parsed.items) >= 4
    page_nos = {i.page_no for i in parsed.items if i.page_no is not None}
    assert 1 in page_nos and 2 in page_nos, f"page provenance missing: {page_nos}"

    assert chunks, "no chunks generated"
    for ch in chunks:
        assert 0 < len(ch["content"]) <= 1000 + 150
        assert ch["page_start"] is not None and ch["page_end"] is not None
    full = " ".join(ch["content"] for ch in chunks)
    assert "Chlorophyll" in full and "thylakoid" in full
