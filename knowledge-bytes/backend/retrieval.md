# Knowledge Bytes: Retrieval

> Source: `backend/app/retrieval.py`
>
> Covers:
> - `retrieve()` — embed → over-fetch → threshold → trim
> - `format_context()` — the numbered `[1]…[n]` context block

---

## Byte 1 — `retrieve()`: the whole algorithm in four lines

### Builds on
[Embeddings](./embeddings.md), [Database](./db.md) (Byte 3: `search_chunks`).

### In plain terms
`retrieve()` embeds the question, asks Postgres for `top_k × 2` candidates, discards everything below the 0.30 similarity threshold, and returns at most `top_k` hits. That's the entire retrieval algorithm.

### Relevant code
`backend/app/retrieval.py`:

```python
def retrieve(question, top_k=None, document_ids=None) -> list[dict]:
    settings = get_settings()
    top_k = top_k or settings.TOP_K
    qvec = embed_query(question)
    hits = db.search_chunks(qvec, top_k * 2, document_ids)  # over-fetch, then threshold
    kept = [h for h in hits if h["similarity"] >= settings.SCORE_THRESHOLD]
    return kept[:top_k]
```

### What's happening
Over-fetching (`top_k × 2`) exists because thresholding happens *after* ranking: if the DB returned exactly 6 and 2 fell below 0.30, you'd only have 4. Fetching 12 gives the threshold room to work while still capping the final list at 6. `document_ids` (the Notebook's scope selector) passes straight through to the SQL `WHERE` clause — scoping is enforced in the database, not in Python.

### Why it matters
This function is the precision/recall control panel of the whole RAG system. The threshold (0.30) decides what counts as "evidence"; `top_k` bounds cost and context size. Note what's *not* here: no reranking, no hybrid search, no query expansion — deliberately simple.

---

## Byte 2 — `format_context()`: numbers become citations

### Builds on
Byte 1.

### In plain terms
`format_context()` turns the hit list into the numbered text block injected into the LLM prompt: `[1] Title, p.3:\n<chunk text>`. The numbers are 1-based, in similarity order, and they're exactly the `[n]` markers the model is instructed to cite.

### Relevant code
```python
def format_context(hits: list[dict]) -> str:
    parts = []
    for i, h in enumerate(hits, start=1):
        label = h["title"] or h["filename"]
        page = f", p.{h['page_start']}" if h.get("page_start") else ""
        parts.append(f"[{i}] {label}{page}:\n{h['content']}")
    return "\n\n".join(parts)
```

### What's happening
Each hit becomes `[i] <title>, p.<page>:\n<full chunk text>`, joined by blank lines. The page suffix is omitted when Docling had no provenance. This string goes inside `<context>…</context>` in the user message (see [LLM](./llm.md)).

### Why it matters
The rank→marker correspondence is the load-bearing convention of the citation system: `routes.py`'s `_to_source_out()` assigns the same 1-based ranks to the Sources panel, so `[2]` in the answer always means the second source card. Change the ordering here and citations silently point at the wrong passages.

---

## Putting It Together

`retrieval.py` is 30 lines with two jobs: `retrieve()` finds evidence (embed → SQL cosine search → threshold → trim, optionally scoped), and `format_context()` numbers it for the LLM. It's called by both chat endpoints in [API](./api.md) and tested by `test_retrieval.py`. The simplicity is intentional — every behavior (threshold, top-k, scoping) maps to one visible line. Next: [LLM](./llm.md) (turning context into answers).
