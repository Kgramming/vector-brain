"""Pytest bootstrap: mock-first settings so unit tests never need a DB, a Groq
key, or a model download. Must run before any `app.*` import."""

import os
import sys
from pathlib import Path

os.environ.setdefault("MOCK_EMBEDDINGS", "true")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.setdefault("UPLOAD_DIR", "/tmp/vectorbrain-test-uploads")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
