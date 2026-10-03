"""
Vector-Brain backend — Knowledge Bytes.

A Knowledge Byte explains ONE component/function/responsibility of technical
content in ~10 seconds, architecture-first. Model-agnostic: this module owns
the template and the prompt; any chat model can fill it.

Format (v2, architecture-first):
    BYTE N — <Component / Function / Responsibility>
    ROLE / FLOW / CONNECTS TO / WHY / KEY CODE
    ... ending with PUTTING IT TOGETHER (3–6 sentence architecture summary).
"""

from __future__ import annotations

BYTE_TEMPLATE = """\
You explain technical/code content as "Knowledge Bytes" for a Vector-Brain user
studying a system. Follow this format EXACTLY.

For the content below, identify the distinct components/functions/
responsibilities (aim for 3–7 bytes, one per major piece). For EACH, output:

BYTE N — <Component / Function / Responsibility>

ROLE:
What does this part do? (1–2 sentences)

FLOW:
Input → Processing → Output (one line, arrows)

CONNECTS TO:
- Uses:
- Used by:
- Architectural layer:

WHY:
Why does it exist? What breaks without it? (1–2 sentences)

KEY CODE:
Only the smallest relevant snippet (max ~10 lines). No line-by-line tutorial.

Rules:
- Architecture first: name the part's place in the system before its details.
- Each byte must be understandable in ~10 seconds. Avoid long explanations.
- No line-by-line code walkthroughs. Snippets only.
- Stay faithful to the provided content; do not invent APIs or behavior.

After the last byte, output:

PUTTING IT TOGETHER
A concise 3–6 sentence summary of how the pieces form the whole architecture.
"""


def build_knowledge_bytes_prompt(content: str, language: str = "", context_note: str = "") -> list[dict]:
    header = "Content to explain:\n"
    if language:
        header += f"Language: {language}\n"
    if context_note:
        header += f"Context: {context_note}\n"
    user = f"{header}\n```\n{content[:20000]}\n```"
    return [
        {"role": "system", "content": BYTE_TEMPLATE},
        {"role": "user", "content": user},
    ]


def render_bytes_preview(content: str) -> str:
    """
    Offline preview of the byte structure (used when no GROQ_API_KEY is set):
    shows the skeleton so the UI stays useful in mock mode.
    """
    lines = [l for l in content.splitlines() if l.strip()][:1]
    first = lines[0][:60] if lines else "content"
    return (
        f"BYTE 1 — {first}\n\nROLE:\n(connect a GROQ_API_KEY to generate real Knowledge Bytes)\n\n"
        "FLOW:\nInput → Processing → Output\n\n"
        "CONNECTS TO:\n- Uses:\n- Used by:\n- Architectural layer:\n\n"
        "WHY:\n\nKEY CODE:\n\nPUTTING IT TOGETHER\n"
    )
