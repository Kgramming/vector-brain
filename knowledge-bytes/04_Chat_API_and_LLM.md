# 04 — Chat API and LLM

Follow the retrieved evidence through the HTTP layer to Groq and back as a streamed, cited answer.

Source files in this byte: `backend/app/api/routes.py` (`chat`, `_stream_answer`, `_to_source_out`), `backend/app/llm.py` (`SYSTEM_PROMPT`, `build_messages`, `stream_chat`, `is_declined`)

---

### Byte 1: No evidence, no LLM call

**Builds on:** `03`

**In plain terms:**
`POST /api/chat` runs `retrieve()` first. If nothing passes the threshold, it returns a canned refusal *without calling Groq* — no cost, no hallucination risk, empty sources, `declined: true`. This is the cheapest grounding guarantee in the system.

**The code:**
```python
# backend/app/api/routes.py
hits = retrieve(question, top_k=req.top_k, document_ids=req.document_ids)
if not hits:
    # No evidence: answer the refusal path without calling the model.
    return StreamingResponse(_declined(), media_type="text/event-stream")
return StreamingResponse(_stream_answer(question, hits), media_type="text/event-stream")
```

---

### Byte 2: The prompt is a contract

**Builds on:** Byte 1

**In plain terms:**
`llm.py`'s system prompt has five rules; three matter: answer *only* from the excerpts, cite every claim as `[n]`, and begin with the exact marker `[DECLINED]` (no citations) when the excerpts lack the answer. `build_messages()` wraps the numbered context in `<context>` tags so the model can tell evidence from the question.

**The code:**
```python
# backend/app/llm.py
SYSTEM_PROMPT = """...
1. Answer ONLY using the excerpts in <context>. Do not use outside knowledge.
2. Cite every factual claim with the excerpt number like [1], [2].
3. If the excerpts do not contain the answer, ... begin your reply with
   the exact marker [DECLINED] and give no citations.
..."""
```

---

### Byte 3: Tokens stream; refusals can't leak citations

**Builds on:** Bytes 1–2

**In plain terms:**
`stream_chat()` POSTs to Groq's OpenAI-compatible endpoint (`openai/gpt-oss-120b`, temperature 0.2, `stream: true`) and yields tokens from the SSE `data:` lines — or a canned mock answer when no API key is set. Back in `routes.py`, `_stream_answer()` buffers the head of the output: if it matches `[DECLINED]`, the marker is consumed server-side and the `sources` event goes out empty. A refusal can never display citations.

**The code:**
```text
Groq SSE → tokens → _stream_answer() → event: sources → event: token* → event: done
                                      (empty if declined — decided before first token)
```

**The code:**
```python
if head.startswith(DECLINE_MARKER):
    declined, decided = True, True
    buf = ""
    yield from emit_sources()  # declined -> no citations
```

Sources are emitted *before* the first token, so the UI renders the Sources panel while the answer is still streaming.

---

### Byte 4: Where to look if answers misbehave

**Builds on:** Bytes 1–3

**In plain terms:**
Wrong citations? Check `format_context()` numbering (`03`, Byte 4) and `_to_source_out()` ranks — they must agree. Model ignoring instructions? Print `build_messages()` output to see exactly what it saw. Refusal showing sources? The stream-level marker detection is the enforcer. Slow answers? Retrieval is milliseconds; the time is Groq.

---

## PUTTING IT TOGETHER

Retrieve first; refuse cheaply on no evidence; prompt with a citation contract; stream tokens with sources-first events; enforce refusal semantics server-side. The model never sees document IDs or scores — only numbered excerpts. `07` shows how the frontend consumes this stream.
