/**
 * Vector-Brain API client.
 * REST via fetch; streaming endpoints via manual SSE parsing over fetch().
 */

const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

function url(path) {
  return `${BASE}${path}`;
}

/** Absolute URL for an API path, respecting VITE_API_URL (for XHR callers). */
export function apiUrl(path) {
  return url(path);
}

async function check(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch { /* ignore */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res;
}

export async function getHealth() {
  const res = await check(await fetch(url('/api/health')));
  return res.json();
}

export async function listDocuments() {
  const res = await check(await fetch(url('/api/documents')));
  return res.json();
}

export async function deleteDocument(id) {
  const res = await check(await fetch(url(`/api/documents/${id}`), { method: 'DELETE' }));
  return res.json();
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await check(await fetch(url('/api/documents'), { method: 'POST', body: form }));
  return res.json();
}

/**
 * Parse a text/event-stream body. handlers: { onSources, onToken, onDone, onError }
 * Events: `sources` (JSON {sources}), `done` (JSON {declined}), `error` (JSON {detail}).
 */
async function readSSE(res, handlers) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  const dispatch = (rawEvent) => {
    const lines = rawEvent.split('\n');
    let event = 'message';
    const dataLines = [];
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    }
    const data = dataLines.join('\n');
    if (!data) return;
    let payload = {};
    try { payload = JSON.parse(data); } catch { /* plain token fallback */ }
    if (event === 'sources') handlers.onSources?.(payload.sources || []);
    else if (event === 'done') handlers.onDone?.(payload);
    else if (event === 'error') handlers.onError?.(new Error(payload.detail || 'Stream error'));
    else if (payload.token !== undefined) handlers.onToken?.(payload.token);
  };
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf('\n\n')) !== -1) {
        const rawEvent = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        dispatch(rawEvent);
      }
    }
    if (buf.trim()) dispatch(buf);
  } finally {
    reader.releaseLock();
  }
}

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

export async function streamKnowledgeBytes({ content, language, context_note }, handlers) {
  const res = await check(await fetch(url('/api/knowledge-bytes'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, language: language || '', context_note: context_note || '' }),
  }));
  await readSSE(res, handlers);
}
