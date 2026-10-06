# Knowledge Bytes: Embeddings

> Source: `backend/app/embeddings.py`
>
> Covers:
> - `_load_model()` — lazy, thread-safe `all-MiniLM-L6-v2` loading
> - `embed_texts()` / `embed_query()` — text → L2-normalized 384-dim vectors
> - `_mock_embed()` — deterministic hash embeddings for tests
> - `cosine_similarity()` — the comparison math

---

## Byte 1 — The model: small, CPU, 384 dimensions

### Builds on
[Configuration](./config.md) (the 384 contract).

### In plain terms
Production embeddings come from `sentence-transformers/all-MiniLM-L6-v2`: a compact model that outputs 384-dimensional vectors, runs on CPU, and is strong enough for semantic search over study documents. It's loaded lazily on first use and cached in a module global.

### Relevant code
`backend/app/embeddings.py`:

```python
_model = None
_model_lock = threading.Lock()

def _load_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:  # double-checked: only one thread loads
                from sentence_transformers import SentenceTransformer
                settings = get_settings()
                # Explicit CPU: avoids Metal/MPS crashes on Apple Silicon.
                _model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _model
```

### What's happening
Double-checked locking: the fast path (`_model is None` check) avoids lock overhead after loading; the lock ensures only one thread builds the model. The comment documents a real incident — concurrent loads corrupted torch's "meta" device tensors during testing with 3 simultaneous uploads. `device="cpu"` is pinned because Apple Silicon's MPS backend crashed on embedding loads.

### Why it matters
Model loading is the slowest part of first ingestion (~tens of seconds for the download). Laziness keeps API startup fast; the lock keeps concurrent uploads safe. This is the only place the transformer model is ever touched.

---

## Byte 2 — `embed_texts()`: batches in, normalized vectors out

### Builds on
Byte 1.

### In plain terms
`embed_texts()` takes a list of strings and returns a list of L2-normalized 384-float vectors — one per input, in order. Normalization is what makes cosine similarity equivalent to a dot product downstream.

### Relevant code
```python
def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    settings = get_settings()
    if settings.MOCK_EMBEDDINGS:
        return _mock_embed(texts, settings.EMBEDDING_DIM)
    model = _load_model()
    arr = model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
    arr = np.asarray(arr, dtype=np.float32)
    if arr.shape[1] != settings.EMBEDDING_DIM:
        raise RuntimeError(f"Embedding dim mismatch: got {arr.shape[1]}, expected {settings.EMBEDDING_DIM}")
    return arr.tolist()
```

### What's happening
Batch encoding (one model call for many texts — the pipeline embeds all chunks at once). `normalize_embeddings=True` L2-normalizes each vector, so pgvector's cosine distance works correctly. The dimension check is the runtime half of the 384 contract from `config.py` (the validator is the boot-time half). `embed_query()` is just `embed_texts([text])[0]` — questions and chunks go through the identical path, which is required for the similarities to be meaningful.

### Why it matters
Every vector in Postgres was born here, and every query vector is born here too. Same model + same normalization on both sides is what makes "similar meaning ≈ nearby vectors" true.

---

## Byte 3 — Mock embeddings: tests without the model

### Builds on
Byte 2.

### In plain terms
When `MOCK_EMBEDDINGS=true`, `_mock_embed()` replaces the transformer with a deterministic hash trick: each token hashes into one of 384 buckets, the vector is L2-normalized. Texts sharing words share buckets, so related texts score higher — enough to exercise retrieval ranking with zero downloads.

### Relevant code
```python
def _mock_embed(texts: Sequence[str], dim: int) -> list[list[float]]:
    out = []
    for text in texts:
        buckets = set()
        for tok in text.lower().split():
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            buckets.add(h % dim)
        vec = [0.0] * dim
        for b in buckets: vec[b] = 1.0
        norm = math.sqrt(len(buckets)) or 1.0
        out.append([v / norm for v in vec])
    return out
```

### What's happening
One binary bucket per token (SHA-256 → mod 384), L2-normalized by the bucket count. It's a sparse bag-of-words in a 384-dim space: identical texts give similarity 1.0, disjoint texts near 0. Deterministic — same text always gives the same vector, so tests are reproducible.

### Why it matters
The backend test suite (`test_retrieval.py`, `test_db_search.py`, …) runs in seconds with no 90 MB model download because of this function. It's explicitly "for tests only" — never used in production unless someone opts in.

---

## Putting It Together

`embeddings.py` is the system's translator between text and geometry: one lazily-loaded MiniLM model, batch encoding with L2 normalization, a hard 384-dimension check, and a hash-based mock for tests. Ingestion calls `embed_texts()` on chunks; retrieval calls `embed_query()` on questions; pgvector compares the results. Next: [Retrieval](./retrieval.md) (finding the right chunks) and [Database](./db.md) (the SQL behind the search).
