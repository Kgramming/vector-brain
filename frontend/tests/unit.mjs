/**
 * Vector-Brain frontend unit tests (no build step, no browser).
 * Run: npm test
 *
 * These test pure logic extracted alongside the components: SSE parsing
 * mirrors the client's readSSE behavior, and citation helpers mirror the
 * chat panel's display logic.
 */

import assert from 'node:assert/strict';

// --- replicate the client's shortName helper (ChatPanel.vue) ---
function shortName(title) {
  const t = title || 'doc';
  return t.length > 22 ? t.slice(0, 20) + '…' : t;
}

// --- replicate SSE event dispatch (services/api.js readSSE) ---
function parseSSE(raw) {
  const events = [];
  for (const chunk of raw.split('\n\n')) {
    if (!chunk.trim()) continue;
    let event = 'message';
    const dataLines = [];
    for (const line of chunk.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    }
    events.push({ event, data: JSON.parse(dataLines.join('\n')) });
  }
  return events;
}

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log(`ok - ${name}`); }
  catch (e) { console.error(`FAIL - ${name}: ${e.message}`); process.exitCode = 1; }
}

test('shortName truncates long titles', () => {
  assert.equal(shortName('a'.repeat(30)), 'a'.repeat(20) + '…');
});

test('shortName keeps short titles', () => {
  assert.equal(shortName('notes.pdf'), 'notes.pdf');
});

test('shortName handles empty title', () => {
  assert.equal(shortName(''), 'doc');
});

test('SSE sources event parses', () => {
  const raw = 'event: sources\ndata: {"sources": [{"rank": 1}]}\n\n';
  const [e] = parseSSE(raw);
  assert.equal(e.event, 'sources');
  assert.equal(e.data.sources[0].rank, 1);
});

test('SSE token + done events parse in order', () => {
  const raw = 'data: {"token": "hello"}\n\ndata: {"token": " world"}\n\nevent: done\ndata: {"declined": false}\n\n';
  const events = parseSSE(raw);
  assert.equal(events.length, 3);
  assert.equal(events[0].data.token, 'hello');
  assert.equal(events[1].data.token, ' world');
  assert.equal(events[2].event, 'done');
  assert.equal(events[2].data.declined, false);
});

test('SSE declined flag parses', () => {
  const raw = 'event: done\ndata: {"declined": true}\n\n';
  const [e] = parseSSE(raw);
  assert.equal(e.data.declined, true);
});

test('SSE error event parses', () => {
  const raw = 'event: error\ndata: {"detail": "Groq API error: boom"}\n\n';
  const [e] = parseSSE(raw);
  assert.equal(e.event, 'error');
  assert.match(e.data.detail, /Groq/);
});

console.log(`\n${passed} tests passed`);
