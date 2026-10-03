"""
Vector-Brain backend — configuration.

All settings come from environment variables (see .env.example).
No secrets are hard-coded anywhere in this repository.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    DATABASE_URL: str = "postgresql://vectorbrain:vectorbrain@localhost:5432/vectorbrain"

    # --- Groq ---
    GROQ_API_KEY: str = ""  # empty => MOCK_GROQ mode (offline/dev)
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # --- Embeddings (384-dimensional, matches pgvector schema) ---
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    MOCK_EMBEDDINGS: bool = False  # deterministic hash embeddings, for tests only

    # --- Retrieval ---
    TOP_K: int = 6
    SCORE_THRESHOLD: float = 0.30  # minimum cosine similarity to count as a citation

    # --- Ingestion ---
    CHUNK_SIZE: int = 1000  # target characters per chunk
    CHUNK_OVERLAP: int = 150  # characters of overlap between chunks
    MAX_UPLOAD_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # --- App ---
    APP_NAME: str = "Vector-Brain"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    @property
    def mock_groq(self) -> bool:
        return not self.GROQ_API_KEY.strip()

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @field_validator("EMBEDDING_DIM")
    @classmethod
    def dim_must_match_schema(cls, v: int) -> int:
        # The pgvector column is vector(384); the embedding model must agree.
        if v != 384:
            raise ValueError("EMBEDDING_DIM must be 384 (pgvector schema is vector(384))")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
