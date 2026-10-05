/**
 * Vector-Brain frontend unit tests (no build step, no browser).
 * Run: npm test
 *
 * These test pure logic extracted alongside the components: SSE parsing
 * mirrors the client's readSSE behavior, and citation helpers mirror the
 * chat panel's display logic.
 */

import assert from 'node:assert/strict';

import { citedRanks, filterSourcesToCited } from '../src/utils/format.js';

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

// --- citation/source consistency (utils/format.js) ---

test('citedRanks extracts [n] markers', () => {
  const ranks = citedRanks('Precision matters [1] and recall too [3].');
  assert.deepEqual([...ranks].sort(), [1, 3]);
});

test('citedRanks dedupes repeats', () => {
  const ranks = citedRanks('[2] again [2] and [10].');
  assert.deepEqual([...ranks].sort((a, b) => a - b), [2, 10]);
});

test('citedRanks ignores non-citations', () => {
  assert.deepEqual([...citedRanks('no markers here')], []);
  assert.deepEqual([...citedRanks('')], []);
  assert.deepEqual([...citedRanks(null)], []);
});

test('filterSourcesToCited keeps only cited sources', () => {
  const sources = [
    { rank: 1, title: 'a.pdf' },
    { rank: 2, title: 'b.pdf' },
    { rank: 3, title: 'c.pdf' },
  ];
  const kept = filterSourcesToCited(sources, 'See [1] and [3].');
  assert.deepEqual(kept.map(s => s.rank), [1, 3]);
});

test('filterSourcesToCited drops everything when nothing cited', () => {
  const sources = [{ rank: 1, title: 'a.pdf' }];
  assert.deepEqual(filterSourcesToCited(sources, 'No citations here.'), []);
});

// --- chat-history upsert logic mirrors useChatHistory.saveConversation ---

function upsertConversation(list, conv) {
  return [conv, ...list.filter(c => c.id !== conv.id)].slice(0, 30);
}

test('history upsert adds new conversation first', () => {
  const list = upsertConversation([], { id: 'c1', title: 'Q1', messages: [] });
  assert.equal(list.length, 1);
  assert.equal(list[0].id, 'c1');
});

test('history upsert updates existing conversation in place', () => {
  const list = [
    { id: 'c2', title: 'Q2', messages: [{ role: 'user', content: 'Q2' }] },
    { id: 'c1', title: 'Q1', messages: [{ role: 'user', content: 'Q1' }] },
  ];
  const updated = upsertConversation(list, {
    id: 'c1', title: 'Q1', messages: [{ role: 'user', content: 'Q1' }, { role: 'assistant', content: 'A1' }],
  });
  assert.equal(updated.length, 2);
  assert.equal(updated[0].id, 'c1');
  assert.equal(updated[0].messages.length, 2);
});

test('history upsert caps at 30 conversations', () => {
  let list = [];
  for (let i = 0; i < 35; i++) list = upsertConversation(list, { id: 'c' + i, title: 't' });
  assert.equal(list.length, 30);
  assert.equal(list[0].id, 'c34');
});

console.log(`\n${passed} tests passed`);
