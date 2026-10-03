"""Unit tests for the Groq chat layer in MOCK mode (no API key, no network)."""

from app import llm
from app.llm import build_messages, chat_once, is_declined, stream_chat, strip_declined_marker


def test_mock_stream_yields_text():
    tokens = list(stream_chat("What is RAG?", "[1] notes.pdf:\nRAG grounds answers."))
    text = "".join(tokens)
    assert len(text) > 20
    assert "mock" in text.lower()


def test_chat_once_concatenates_stream():
    answer = chat_once("q", "[1] x:\ny")
    assert isinstance(answer, str) and len(answer) > 0


def test_declined_detection():
    assert is_declined("[DECLINED] I cannot answer from the context.")
    assert not is_declined("The answer is [1].")


def test_strip_declined_marker():
    assert strip_declined_marker("[DECLINED]  no info") == "no info"


def test_system_prompt_demands_citations_and_marker():
    msgs = build_messages("q", "[1] x:\ny")
    system = msgs[0]["content"]
    assert "[DECLINED]" in system
    assert "[1]" in system
    assert msgs[1]["role"] == "user"
    assert "<context>" in msgs[1]["content"]


def test_streaming_refusal_head_detection():
    """A model reply starting with [DECLINED]: the SSE stream must consume the
    marker, flag declined, and never leak the marker into visible tokens."""
    import json

    from app.api import routes as routes_module

    def fake_stream(question, context):
        yield "[DECLINED]"
        yield " Sorry, "
        yield "not in the docs."

    orig_stream = routes_module.stream_chat
    orig_format = routes_module.format_context
    routes_module.stream_chat = fake_stream
    routes_module.format_context = lambda hits: ""
    try:
        events = list(routes_module._stream_answer("q", []))
    finally:
        routes_module.stream_chat = orig_stream
        routes_module.format_context = orig_format

    tokens, dones = [], []
    for ev in events:
        for line in ev.splitlines():
            if line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                if "token" in payload:
                    tokens.append(payload["token"])
            if line.startswith("event: done"):
                dones.append(ev)
    text = "".join(tokens)
    assert "[DECLINED]" not in text
    assert "not in the docs." in text
    assert '"declined": true' in "".join(dones)


def test_streaming_normal_answer_not_declined():
    """A normal reply streams through untouched with declined=false."""
    import json

    from app.api import routes as routes_module

    def fake_stream(question, context):
        yield "Photosynthesis "
        yield "happens in chloroplasts [1]."

    orig_stream = routes_module.stream_chat
    orig_format = routes_module.format_context
    routes_module.stream_chat = fake_stream
    routes_module.format_context = lambda hits: ""
    try:
        events = list(routes_module._stream_answer("q", []))
    finally:
        routes_module.stream_chat = orig_stream
        routes_module.format_context = orig_format

    text = "".join(
        json.loads(l[5:].strip())["token"]
        for ev in events for l in ev.splitlines()
        if l.startswith("data:") and "token" in l
    )
    assert text == "Photosynthesis happens in chloroplasts [1]."
    assert '"declined": false' in "".join(events)
