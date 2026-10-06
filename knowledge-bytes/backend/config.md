# Knowledge Bytes: Configuration

> Source: `backend/app/config.py`, `.env.example` (documents the variables)
>
> Covers:
> - `Settings` — every tunable in one place
> - `get_settings()` — cached singleton access
> - Mock modes (`mock_groq`, `MOCK_EMBEDDINGS`)

---

## Byte 1 — One class, every knob

### Builds on
[System Overview](../architecture/system-overview.md) (Byte 2).

### In plain terms
`config.py` defines a single `Settings` class (via `pydantic-settings`) holding every backend tunable: database URL, Groq credentials, embedding model, retrieval parameters, chunking parameters, and upload limits. Values come from the environment or `.env`; nothing is hard-coded.

### Relevant code
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    TOP_K: int = 6
    SCORE_THRESHOLD: float = 0.30
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_MB: int = 50
```

### What's happening
Each field is an environment variable with a sane default. `extra="ignore"` means stray env vars don't crash the app. The defaults encode the system's tested operating point: 1000-char chunks, top-6 retrieval, 0.30 cosine cutoff.

### Why it matters
This file is the answer to "what numbers does the system use?" — and changing behavior (e.g. a stricter threshold) starts here, not in code.

---

## Byte 2 — The 384 contract

### Builds on
Byte 1.

### In plain terms
A Pydantic validator refuses to boot with any `EMBEDDING_DIM` other than 384, because the Postgres column is `vector(384)` and the MiniLM model outputs 384 dimensions. All three must agree.

### Relevant code
```python
@field_validator("EMBEDDING_DIM")
@classmethod
def dim_must_match_schema(cls, v: int) -> int:
    # The pgvector column is vector(384); the embedding model must agree.
    if v != 384:
        raise ValueError("EMBEDDING_DIM must be 384 (pgvector schema is vector(384))")
    return v
```

### What's happening
At startup, if someone sets `EMBEDDING_DIM=768`, the app raises immediately instead of failing obscurely on the first insert (pgvector would reject the wrong-sized vector). The comment names the three parties: model output, setting, SQL schema.

### Why it matters
Embedding dimension mismatches are a classic silent-corruption bug in RAG systems. This validator turns it into a loud, instant failure. See [Embeddings](./embeddings.md) and [Database](./db.md) for the other two sides of the contract.

---

## Byte 3 — Mock modes: the app runs with nothing

### Builds on
Byte 1.

### In plain terms
Two flags let the whole system run offline: an empty `GROQ_API_KEY` enables mock LLM answers (`mock_groq` property), and `MOCK_EMBEDDINGS=true` swaps the transformer model for deterministic hash vectors. Tests and demos use these; production sets a real key.

### Relevant code
```python
@property
def mock_groq(self) -> bool:
    return not self.GROQ_API_KEY.strip()
```

```python
MOCK_EMBEDDINGS: bool = False  # deterministic hash embeddings, for tests only
```

### What's happening
`mock_groq` is derived — there's no separate flag to get wrong. `llm.py` checks it to decide between `_mock_stream` (canned, citation-shaped text) and the real Groq call; `embeddings.py` checks `MOCK_EMBEDDINGS` to decide between hash vectors and `all-MiniLM-L6-v2`. The `/api/health` endpoint reports `groq_mode: mock|live` so the UI can show a banner.

### Why it matters
The entire test suite (`backend/tests/`) runs with no network, no GPU, and no API key because of these two flags. They also make the demo safe: clone, `docker-compose up`, run — no secrets needed.

---

## Putting It Together

`config.py` is small on purpose: one validated, cached settings object that the rest of the backend imports. The 384-dimension contract and the mock-mode derivations are the only "logic" here — everything else is declarative. When debugging behavior, check these values first.
