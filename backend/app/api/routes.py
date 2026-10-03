"""
Vector-Brain backend — HTTP API.

- POST /api/documents        upload a PDF (202 + background ingestion)
- GET  /api/documents        list documents with status
- DELETE /api/documents/{id} delete document + its chunks
- POST /api/chat             streaming SSE answer with citations
- POST /api/chat/sync        non-streaming JSON answer (tests, simple clients)
- POST /api/knowledge-bytes  streaming Knowledge Bytes for pasted code/content
- GET  /api/health           service + dependency status
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .. import db
from ..config import get_settings
from ..knowledge_bytes import build_knowledge_bytes_prompt, render_bytes_preview
from ..llm import chat_once, is_declined, stream_chat, strip_declined_marker
from ..pipeline import process_upload
from ..retrieval import format_context, retrieve

router = APIRouter(prefix="/api")
settings = get_settings()


# ------------------------------------------------------------------ models

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatSyncResponse(BaseModel):
    answer: str
    declined: bool
    sources: list[dict]


class KnowledgeBytesRequest(BaseModel):
    content: str = Field(min_length=1, max_length=60000)
    language: str = Field(default="", max_length=50)
    context_note: str = Field(default="", max_length=500)


def _to_source_out(hits: list[dict]) -> list[dict]:
    return [
        {
            "rank": i,
            "document_id": str(h["document_id"]),
            "filename": h["filename"],
            "title": h["title"] or h["filename"],
            "chunk_index": h["chunk_index"],
            "page_start": h["page_start"],
            "page_end": h["page_end"],
            "similarity": round(float(h["similarity"]), 4),
            "excerpt": h["content"][:500],
        }
        for i, h in enumerate(hits, start=1)
    ]


# ------------------------------------------------------------------ health

@router.get("/health")
def health() -> dict:
    try:
        docs = db.list_documents()
        chunks = db.count_chunks()
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        docs, chunks, db_ok = [], 0, False
        db_error = str(exc)
    else:
        db_error = None
    return {
        "status": "ok" if db_ok else "degraded",
        "groq_mode": "mock" if settings.mock_groq else "live",
        "documents": len(docs),
        "chunks": chunks,
        "db_error": db_error,
    }


# ------------------------------------------------------------------ documents

@router.get("/documents")
def list_documents() -> dict:
    return {"documents": db.list_documents()}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    if not db.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": doc_id}


@router.post("/documents", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> dict:
    name = file.filename or "upload.pdf"
    if not (name.lower().endswith(".pdf") or file.content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    sha256 = hashlib.sha256(data).hexdigest()
    existing = [d for d in db.list_documents() if d.get("sha256") == sha256 and d["status"] == "ready"]
    if existing:
        raise HTTPException(status_code=409, detail="This PDF is already in your library")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / f"{uuid.uuid4().hex}.pdf"
    saved_path.write_bytes(data)

    doc = db.create_document(filename=name, title=name, file_size=len(data), sha256=sha256)
    background_tasks.add_task(process_upload, str(doc["id"]), str(saved_path))
    return {"id": str(doc["id"]), "filename": name, "status": "processing"}


# ------------------------------------------------------------------ chat

DECLINE_MARKER = "[DECLINED]"


def _stream_answer(question: str, hits: list[dict]):
    """
    SSE stream. First event carries the sources; then tokens; then a done
    event with the declined flag. A leading [DECLINED] marker is consumed
    server-side (never streamed) so refusals carry no citations.

    Detection is prefix-exact: we buffer until the head either matches the
    marker or provably diverges from it (decided within ~len(marker) chars),
    so a refusal can never leak the marker into the visible answer.
    """
    yield f"event: sources\ndata: {json.dumps({'sources': _to_source_out(hits)})}\n\n"

    context = format_context(hits)
    buf = ""
    declined = False
    decided = False

    def emit(text: str):
        if text:
            yield f"data: {json.dumps({'token': text})}\n\n"

    try:
        token_iter = stream_chat(question, context)
        for token in token_iter:
            if not decided:
                buf += token
                head = buf.lstrip()
                if head.startswith(DECLINE_MARKER):
                    declined, decided = True, True
                    rest = head[len(DECLINE_MARKER):]
                    buf = ""
                    yield from emit(rest)
                    continue
                if len(head) >= len(DECLINE_MARKER) or not DECLINE_MARKER.startswith(head):
                    decided = True  # head provably isn't the marker
                    yield from emit(buf)
                    buf = ""
                continue
            yield from emit(token)
        yield from emit(buf)  # short answers that never resolved the head check
    except RuntimeError as exc:
        yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
        return
    yield f"event: done\ndata: {json.dumps({'declined': declined})}\n\n"


@router.post("/chat")
def chat(req: ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")
    hits = retrieve(question, top_k=req.top_k)
    if not hits:
        # No evidence: answer the refusal path without calling the model.
        def _declined():
            yield f"event: sources\ndata: {json.dumps({'sources': []})}\n\n"
            yield f"data: {json.dumps({'token': 'I couldn’t find anything about that in your documents. Try uploading the relevant PDF first.'})}\n\n"
            yield f"event: done\ndata: {json.dumps({'declined': True})}\n\n"

        return StreamingResponse(_declined(), media_type="text/event-stream")
    # Groq failures surface mid-stream as `event: error` (see _stream_answer).
    return StreamingResponse(_stream_answer(question, hits), media_type="text/event-stream")


@router.post("/chat/sync", response_model=ChatSyncResponse)
def chat_sync(req: ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is empty")
    hits = retrieve(question, top_k=req.top_k)
    if not hits:
        return ChatSyncResponse(
            answer="I couldn’t find anything about that in your documents. Try uploading the relevant PDF first.",
            declined=True,
            sources=[],
        )
    try:
        raw = chat_once(question, format_context(hits))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    declined = is_declined(raw)
    return ChatSyncResponse(
        answer=strip_declined_marker(raw),
        declined=declined,
        sources=[] if declined else _to_source_out(hits),
    )


# ------------------------------------------------------------------ knowledge bytes

@router.post("/knowledge-bytes")
def knowledge_bytes(req: KnowledgeBytesRequest):
    content = req.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Content is empty")

    def _gen():
        if settings.mock_groq:
            preview = render_bytes_preview(content)
            for word in preview.split(" "):
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        messages = build_knowledge_bytes_prompt(content, req.language, req.context_note)
        import httpx

        payload = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        try:
            with httpx.stream(
                "POST",
                f"{settings.GROQ_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=180.0,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"]
                    except (KeyError, IndexError, ValueError):
                        continue
                    token = delta.get("content")
                    if token:
                        yield f"data: {json.dumps({'token': token})}\n\n"
        except httpx.HTTPError as exc:
            yield f"event: error\ndata: {json.dumps({'detail': f'Groq API error: {exc}'})}\n\n"
            return
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")
