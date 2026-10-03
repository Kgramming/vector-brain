"""Unit tests for the overlapping chunker (no Docling, no DB needed)."""

import pytest

from app.config import get_settings
from app.ingest import TextItem, chunk_items


def items(n_pages=3, per_page=4):
    out = []
    for p in range(1, n_pages + 1):
        for i in range(per_page):
            out.append(TextItem(text=f"Page {p} sentence {i} about vector databases. ", page_no=p))
    return out


def test_chunks_cover_all_text():
    chunks = chunk_items(items(), chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 1
    # every page's text appears in at least one chunk
    joined = " ".join(c["content"] for c in chunks)
    for p in range(1, 4):
        assert f"Page {p} sentence 0" in joined


def test_chunk_size_respected():
    chunks = chunk_items(items(), chunk_size=300, chunk_overlap=50)
    for c in chunks:
        assert len(c["content"]) <= 300 + 50  # overlap tail may push slightly over


def test_page_spans_recorded():
    chunks = chunk_items(items(n_pages=2, per_page=2), chunk_size=120, chunk_overlap=20)
    for c in chunks:
        assert c["page_start"] is not None
        assert c["page_end"] is not None
        assert c["page_start"] <= c["page_end"]


def test_overlap_carries_text_forward():
    its = [TextItem(text="alpha " * 60, page_no=1), TextItem(text="beta " * 60, page_no=1)]
    chunks = chunk_items(its, chunk_size=200, chunk_overlap=60)
    assert len(chunks) >= 2
    # the tail of chunk 0 reappears at the head of chunk 1
    assert chunks[0]["content"][-30:] in chunks[1]["content"]


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_items(items(), chunk_size=100, chunk_overlap=100)


def test_empty_items_yield_no_chunks():
    assert chunk_items([]) == []


def test_single_long_item_is_hard_split():
    its = [TextItem(text="word " * 500, page_no=2)]
    chunks = chunk_items(its, chunk_size=200, chunk_overlap=20)
    assert len(chunks) >= 4
    assert all(c["page_start"] == 2 for c in chunks)


def test_missing_page_numbers_tolerated():
    its = [TextItem(text="no provenance here", page_no=None)]
    chunks = chunk_items(its, chunk_size=200, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0]["page_start"] is None


def test_default_settings_from_config():
    s = get_settings()
    chunks = chunk_items(items(n_pages=1, per_page=2))
    assert all(len(c["content"]) <= s.CHUNK_SIZE + s.CHUNK_OVERLAP for c in chunks)
