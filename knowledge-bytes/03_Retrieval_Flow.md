# 03 — Retrieval Flow

Follow a question from text to ranked evidence. If an answer cites the wrong passage, the bug is in this chain.

Source files in this byte: `backend/app/retrieval.py` (`retrieve`, `format_context`), `backend/app/db.py` (`search_chunks`), `backend/app/embeddings.py` (`embed_query`)

---

### Byte 1: The question becomes a vector

**Builds on:** `01`, `02` (Byte 4)

**In plain terms:**
`retrieve()` starts by embedding the question with the *same* model and normalization used for chunks (`embed_query()` → `embed_texts([text])[0]`). Same model on both sides is what makes "similar meaning ≈ nearby vectors" true.

**The code:**
```text
question → embed_query() → 384-dim vector → db.search_chunks(vector, ...)
```

---

### Byte 2: Postgres finds the nearest chunks

**Builds on:** Byte 1

**In plain terms:**
`db.search_chunks()` runs one SQL query: cosine distance (`<=>`) against the `ivfflat` index, converted to similarity (`1 - distance`), joined to document titles, limited to `ready` documents — and, when the Notebook has a document scope selected, restricted to those IDs in the `WHERE` clause.

**The code:**
```sql
-- backend/app/db.py → search_chunks()
SELECT c.id, c.document_id, c.chunk_index, c.page_start, c.page_end,
       c.content, d.filename, d.title,
       1 - (c.embedding <=> %s::vector) AS similarity
FROM chunks c JOIN documents d ON d.id = c.document_id
WHERE d.status = 'ready' [AND c.document_id = ANY(%s::uuid[])]
ORDER BY c.embedding <=> %s::vector
LIMIT %s
```

Scoping is enforced in SQL, not Python — the UI can't leak cross-document passages even if it tried.

---

### Byte 3: Over-fetch, threshold, trim

**Builds on:** Byte 2

**In plain terms:**
`retrieve()` asks for `top_k × 2` candidates, drops everything below the 0.30 similarity threshold, and keeps at most `top_k`. Over-fetching exists because thresholding happens *after* ranking — fetching 12 lets the cutoff work without starving the final list.

**The code:**
```python
# backend/app/retrieval.py — the whole algorithm
hits = db.search_chunks(qvec, top_k * 2, document_ids)  # over-fetch, then threshold
kept = [h for h in hits if h["similarity"] >= settings.SCORE_THRESHOLD]
return kept[:top_k]
```

No reranking, no hybrid search, no query expansion — deliberately simple. The threshold is the precision/recall knob of the entire RAG system.

---

### Byte 4: Numbers become citations

**Builds on:** Byte 3

**In plain terms:**
`format_context()` turns the hits into the numbered block injected into the LLM prompt: `[1] Title, p.3:` followed by the chunk text. These 1-based ranks are exactly the `[n]` markers the model is told to cite — and `routes.py` assigns the same ranks to the Sources panel, so `[2]` in an answer always means the second source card.

**The code:**
```python
parts.append(f"[{i}] {label}{page}:\n{h['content']}")  # i starts at 1
```

---

## PUTTING IT TOGETHER

Embed the question → cosine-search Postgres (scoped, ready-only) → over-fetch → threshold at 0.30 → trim to top-K → number the survivors as `[1]…[n]`. What comes out is *evidence*; `04` shows how it becomes an answer.
