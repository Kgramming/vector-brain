# Vector-Brain — Evaluation Guide

How to judge whether the RAG pipeline is actually working (not just fluent).

## Retrieval quality checks

1. **Precision probe.** Upload a PDF, then ask a question whose answer is a
   distinctive phrase from one page. The top source's excerpt should contain
   that phrase, with `similarity` well above `SCORE_THRESHOLD` (default 0.30).

2. **Cross-document recall.** Ask a question needing facts from two PDFs.
   Sources should cite **both** documents (check `filename` on each source).

3. **Negative probe.** Ask about something absent from the library.
   Expected: declined answer, `declined: true`, **zero sources**. Any citation
   here is a failure — the refusal path must not attach evidence.

4. **Threshold behavior.** Lower `SCORE_THRESHOLD` to `0.0` and repeat the
   negative probe: you should now get low-similarity sources instead of a
   decline. This confirms the threshold (not the LLM) drives refusals.

## Answer quality checks

- Every factual claim in the answer carries a `[n]` marker.
- Markers point at the right excerpt (spot-check 2–3).
- No outside knowledge leaks: ask about a topic where the PDF disagrees with
  common knowledge; the answer must follow the PDF.

## Ingestion checks

- Multi-page PDF → `page_count > 1`, chunks have `page_start/page_end`.
- Re-upload same file → `409`, chunk count unchanged.
- Corrupt PDF → `status: failed` with an error message (never stuck on
  `processing`).
- 50+ MB file → `413`.

## Automated

```bash
cd backend
.venv/bin/python -m pytest tests/ -q            # unit suite (mocked, offline)
npm test --prefix ../frontend                   # frontend unit tests
# With a real DB:
VECTORBRAIN_TEST_DATABASE_URL=postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain_test \
  .venv/bin/python -m pytest tests/test_db_integration.py -v
```

## Known limitations (honest)

- Docling parsing is CPU-heavy; very large PDFs take minutes (background task).
- `ivfflat` index lists=100 suits corpora up to ~1M chunks; beyond that, retune.
- Mock Groq answers are placeholders, clearly labeled in the UI.
- No per-user auth — single-user study tool by design (see ARCHITECTURE.md
  scaling notes for the multi-tenant path).
