# Knowledge Bytes: Frontend API Services

> Source: `frontend/src/services/api.js`
>
> Covers:
> - `getHealth()` / `listDocuments()` / `deleteDocument()` / `uploadDocument()`
> - `streamChat()` — SSE streaming over `fetch()`
> - `readSSE()` — manual event parsing

---

## Byte 1 — Thin REST wrappers

### Builds on
[Frontend Architecture](./architecture.md).

### In plain terms
`api.js` exports one async function per backend endpoint. Each does a `fetch`, throws a rich `Error` (with HTTP `status`) on failure, and returns parsed JSON. The base URL comes from `VITE_API_URL`, defaulting to same-origin (which is why the Vite dev proxy works with no config).

### Relevant code
```js
const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

async function check(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = body.detail || detail; }
    catch { /* ignore */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res;
}

export async function listDocuments() {
  const res = await check(await fetch(url('/api/documents')));
  return res.json();
}
```

### What's happening
`check()` centralizes error handling: it prefers the backend's `{"detail": …}` message (so a `409` surfaces "This PDF is already in your library", not "Conflict"). Callers (`useLibrary`, `UploadModal`, `NotebookView`) never touch `fetch` directly.

### Why it matters
Every backend interaction flows through these five functions — if the API changes, this file is the only frontend code that must change.

---

## Byte 2 — `streamChat()`: SSE without EventSource

### Builds on
Byte 1, [API](../backend/api.md) (Byte 3: the chat endpoint).

### In plain terms
`streamChat(question, handlers, { topK, documentIds })` POSTs to `/api/chat` and parses the streaming response manually, calling `onSources`, `onToken`, `onDone`, or `onError` as events arrive. It uses `fetch` + `ReadableStream` instead of `EventSource` because the request needs a JSON POST body.

### Relevant code
```js
export async function streamChat(question, handlers, { topK, documentIds } = {}) {
  const res = await check(await fetch(url('/api/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      top_k: topK ?? null,
      document_ids: documentIds && documentIds.length ? documentIds : null,
    }),
  }));
  await readSSE(res, handlers);
}
```

### What's happening
`document_ids` is sent as `null` when the Notebook scope is "all documents" (backend treats null as "search everything"); otherwise the selected IDs go through — this is the client half of server-side scoping. `top_k` comes from the notebook preferences.

### Why it matters
This function is the read path's frontend entrypoint. The handler pattern (`onSources`/`onToken`/`onDone`) lets `NotebookView` update three different pieces of UI from one stream.

---

## Byte 3 — `readSSE()`: parsing the event stream

### Builds on
Byte 2.

### In plain terms
`readSSE()` reads the response body chunk by chunk, splits on blank lines (`\n\n` — the SSE event delimiter), and dispatches: `event: sources` → `onSources`, `event: done` → `onDone`, `event: error` → `onError`, anything else with a `token` → `onToken`.

### Relevant code
```js
const dispatch = (rawEvent) => {
  const lines = rawEvent.split('\n');
  let event = 'message';
  const dataLines = [];
  for (const line of lines) {
    if (line.startsWith('event:')) event = line.slice(6).trim();
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
  }
  ...
  if (event === 'sources') handlers.onSources?.(payload.sources || []);
  else if (event === 'done') handlers.onDone?.(payload);
  else if (event === 'error') handlers.onError?.(new Error(payload.detail || 'Stream error'));
  else if (payload.token !== undefined) handlers.onToken?.(payload.token);
};
```

### What's happening
A `TextDecoder` accumulates bytes into a string buffer; each complete `\n\n`-terminated event is dispatched immediately, so tokens render the moment they arrive. The `?.` optional calls mean callers only implement the handlers they need. A trailing partial buffer is flushed at stream end.

### Why it matters
The backend emits sources *before* the first token (see [API](../backend/api.md) Byte 4) — because parsing is incremental, the Sources panel can populate while the answer is still streaming. This file is also why `NotebookView` never needs to know SSE syntax.

---

## Putting It Together

`api.js` is the frontend's entire HTTP layer: five REST helpers with uniform errors, plus a manual SSE client for streaming chat. Views and composables call these functions; they never construct URLs or parse event streams themselves. Next: [Library](./library.md) (upload + document management) and [Notebook](./notebook.md) (the chat UI that consumes the stream).
