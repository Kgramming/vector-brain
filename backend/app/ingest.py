"""
Vector-Brain backend — PDF ingestion with Docling.

Pipeline: PDF bytes -> Docling DocumentConverter -> reading-order text items
with page provenance -> overlapping character chunks (page_start/page_end kept).

The Docling converter is constructed lazily and is injectable
(`get_converter` parameter) so tests can run without the heavy dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .config import get_settings


@dataclass
class TextItem:
    text: str
    page_no: int | None


@dataclass
class ParsedDocument:
    title: str
    page_count: int
    items: list[TextItem]


def _docling_extract(pdf_path: str) -> ParsedDocument:
    """Real extraction path using Docling. Imported lazily (heavy dependency)."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    title = (doc.name or "").strip() or "Untitled document"
    items: list[TextItem] = []
    # texts in reading order; prov carries page provenance when available
    for element, _level in doc.iterate_items():
        txt = getattr(element, "text", None)
        if not txt or not txt.strip():
            continue
        page_no: int | None = None
        prov = getattr(element, "prov", None)
        if prov:
            try:
                first = prov[0]
                page_no = getattr(first, "page_no", None)
            except (IndexError, TypeError):
                page_no = None
        items.append(TextItem(text=txt.strip(), page_no=page_no))

    page_count = len(getattr(doc, "pages", {}) or {})
    return ParsedDocument(title=title, page_count=page_count, items=items)


def parse_pdf(
    pdf_path: str,
    extractor: Callable[[str], ParsedDocument] | None = None,
) -> ParsedDocument:
    """
    Parse a PDF file into ordered text items with page numbers.

    `extractor` overrides the Docling path (used by tests). Pass a callable
    returning a ParsedDocument, or None to use Docling.
    """
    extract = extractor or _docling_extract
    parsed = extract(pdf_path)
    if not parsed.items:
        raise ValueError("No extractable text found in PDF")
    return parsed


def chunk_items(
    items: Sequence[TextItem],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict]:
    """
    Greedy overlapping chunker over reading-order text items.

    Accumulates items until adding the next would exceed chunk_size, then
    emits a chunk. Overlap is achieved by carrying the tail of the previous
    chunk (up to chunk_overlap chars) into the next one. page_start/page_end
    span the pages covered by the chunk.
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    if chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    chunks: list[dict] = []
    buf_parts: list[str] = []
    buf_len = 0
    buf_pages: list[int] = []

    def flush() -> None:
        nonlocal buf_parts, buf_len, buf_pages
        content = " ".join(buf_parts).strip()
        if content:
            pages = [p for p in buf_pages if p is not None]
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "content": content,
                    "page_start": min(pages) if pages else None,
                    "page_end": max(pages) if pages else None,
                }
            )
        # carry overlap tail into the next chunk
        tail = content[-chunk_overlap:] if chunk_overlap else ""
        buf_parts = [tail] if tail else []
        buf_len = len(tail)
        buf_pages = []

    for item in items:
        text = " ".join(item.text.split())  # normalize whitespace
        if not text:
            continue
        # Oversized items are pre-split into chunk-sized pieces with overlap,
        # then flow through the normal accumulation logic below.
        if len(text) > chunk_size:
            pieces, start = [], 0
            while start < len(text):
                pieces.append(text[start : start + chunk_size])
                if start + chunk_size >= len(text):
                    break
                start += chunk_size - chunk_overlap
        else:
            pieces = [text]
        for piece in pieces:
            if buf_len + len(piece) + 1 > chunk_size and buf_parts:
                flush()
            buf_parts.append(piece)
            buf_len += len(piece) + 1
            if item.page_no is not None:
                buf_pages.append(item.page_no)

    flush()
    # re-index after flush (flush appends in order already, but be explicit)
    for i, ch in enumerate(chunks):
        ch["chunk_index"] = i
    return chunks


def ingest_pdf(pdf_path: str, extractor: Callable[[str], ParsedDocument] | None = None) -> tuple[ParsedDocument, list[dict]]:
    """Full ingestion step: parse -> chunk. Embeddings/storage happen in the API layer."""
    parsed = parse_pdf(pdf_path, extractor=extractor)
    chunks = chunk_items(parsed.items)
    return parsed, chunks
