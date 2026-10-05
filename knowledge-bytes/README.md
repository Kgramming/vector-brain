# Knowledge Bytes

A model-agnostic methodology for understanding unfamiliar code, one small piece at a time.

## What are Knowledge Bytes?

A Knowledge Byte is a small, self-contained explanation of a single concept,
function, code block, or responsibility inside an unfamiliar codebase. Instead of
asking a language model to "explain this code" and receiving a wall of text,
you ask it to break the code into a sequence of short, progressive bytes, each
readable in about 45 seconds.

Each byte follows the same structure:

- **Builds on** — which earlier bytes this one assumes
- **In plain terms** — what it is, in one or two jargon-free sentences
- **The code** — the relevant snippet, nothing more
- **What's happening** — how the snippet works
- **Why it matters** — what it does (the WHAT) and why it exists (the WHY)

The sequence ends with a **PUTTING IT TOGETHER** section that synthesizes the
bytes into one coherent mental model of the whole.

The methodology is defined entirely by a prompt: [knowledge-bytes-prompt.md](knowledge-bytes-prompt.md).
It works with any capable language model and requires no tools, plugins, or
application integration.

## Why this methodology exists

Reading unfamiliar code is one of the most common and most painful parts of
software work: joining a team, reviewing a pull request, debugging a library you
did not write, or revisiting your own code months later.

The usual options are both flawed:

1. **Read the raw code top to bottom.** Slow, and easy to drown in details
   before understanding what the code is even for.
2. **Ask a model for a full explanation.** Fast, but the result is usually a
   long, flat summary that mixes purpose, mechanics, and trivia with no sense
   of what to learn first.

Knowledge Bytes fixes the ordering problem. It enforces a deliberate
progression — context and purpose first, then structure, then details, and edge
cases and gotchas last — so each new piece of information lands on a foundation
the reader already has. Small units respect attention: a 45-second byte is easy
to re-read, easy to question, and easy to skip if you already know it. And by
requiring every byte to state WHAT the code does and WHY it exists, the method
pushes past mechanical line-by-line narration toward real understanding.

## How to use it

Works with ChatGPT, Gemini, Claude, local models (Ollama, LM Studio, llama.cpp,
or anything with a sufficient context window), or any other instruction-following
model.

1. Open [knowledge-bytes-prompt.md](knowledge-bytes-prompt.md) and copy the
   entire prompt.
2. Paste it into a fresh conversation with the model of your choice.
3. Paste the code you want to understand after the prompt (one file, one
   module, or one focused section at a time — see the note on size below).
4. Read the bytes in order. Ask follow-up questions about any single byte
   without losing the thread of the rest.

**A note on size:** the method works best on focused units of code — a file, a
class, a module, or a single feature's worth of functions. If you paste an
entire repository, even a good model will be forced to skim. For large
codebases, run the prompt once per file or per subsystem and treat each run's
PUTTING IT TOGETHER as a byte in a larger map you assemble yourself. With local
models, stay comfortably inside the model's context window; when in doubt,
paste less code per run.

## Expected output format

Every run produces the same shape:

```text
BYTE 1: <short title>
Builds on: nothing — this is the starting point
In plain terms: ...
The code:
    <relevant snippet>
What's happening: ...
Why it matters: ...

BYTE 2: <short title>
Builds on: Byte 1
...

PUTTING IT TOGETHER
<synthesis: how the bytes connect, the end-to-end flow,
 and a one-paragraph mental model of the whole>
```

Bytes are ordered progressively: purpose and context first, structural overview
next, important details after that, and edge cases and gotchas last. Each byte
takes roughly 45 seconds to read.

## Example

See [examples/example.md](examples/example.md) for a complete worked example:
the prompt applied to a small Python retry-with-backoff helper, producing four
bytes plus the final synthesis.

## Tips

- **Challenge a byte.** If "Why it matters" feels thin, ask the model for the
  concrete failure that would occur without that piece of code.
- **Reorder for your goal.** Debugging? Read the gotchas byte first, then work
  backward. Onboarding? Read in order.
- **Use it on your own code.** Explaining a tricky function you wrote six
  months ago is an excellent test of whether the prompt — and your code —
  holds up.
