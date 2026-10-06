# Knowledge Bytes: Notebook (Chat)

> Source: `frontend/src/views/NotebookView.vue`, `frontend/src/utils/format.js`, `frontend/src/utils/markdown.js`
>
> Covers:
> - `send()` — the question → stream → persist flow
> - Document scope selector (`selectedIds`, `document_ids`)
> - Citation filtering (`filterSourcesToCited`) and the Sources panel
> - Conversation persistence (`persistCurrent`, `openConversation`, `newChat`)

---

## Byte 1 — `send()`: one question, end to end

### Builds on
[Services](./services.md) (Byte 2: `streamChat`).

### In plain terms
`send()` pushes the user message, appends an empty assistant message, and calls `streamChat()` with three handlers: `onSources` fills the Sources panel, `onToken` appends text (rendered as Markdown), `onDone` finalizes — filtering sources to cited ranks, marking declined, and persisting the conversation.

### Relevant code
`frontend/src/views/NotebookView.vue`:

```js
const docIds = allSelected.value ? null : [...selectedIds.value];
await streamChat(q, {
  onSources: (s) => { ans.sources = s; },
  onToken: (t) => { ans.content += t; scrollDown(); },
  onDone: ({ declined }) => {
    ans.declined = !!declined;
    ans.streaming = false;
    // Strict grounding: the Sources panel must correspond exactly to the
    // citations the model emitted — drop retrieved-but-uncited passages.
    ans.sources = ans.declined ? [] : filterSourcesToCited(ans.sources, ans.content);
    ...
    persistCurrent();
    scrollDown();
  },
  onError: (e) => { throw e; },
}, { topK: notebookPrefs.value.topK, documentIds: docIds });
```

### What's happening
The assistant message is mutated *through the reactive proxy* (`messages.value[…]`) so the UI updates per token. `documentIds` is `null` when "All documents" is checked (backend searches everything) or the explicit selection otherwise. `onDone` is where client-side grounding is enforced (next byte) and where the conversation is saved.

### Why it matters
This is the read path's UI half: every backend SSE event from [API](../backend/api.md) lands in exactly one of these handlers. The `streaming` flag drives the blinking caret and disables the composer mid-answer.

---

## Byte 2 — Scope: searching a subset

### Builds on
Byte 1, [Retrieval](../backend/retrieval.md).

### In plain terms
The left panel lists `readyDocs` with checkboxes. `selectedIds` (a `Set`) is the scope; `allSelected` is derived. Unchecking "All documents" then picking one PDF makes the next question search only that PDF — enforced server-side by `document_ids`.

### Relevant code
```js
const allSelected = computed(() =>
  readyDocs.value.length > 0 && selectedIds.value.size === readyDocs.value.length);
function toggleDoc(id) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id); else next.add(id);
  selectedIds.value = next;
}
```

### What's happening
A `Set` (replaced, not mutated, to trigger reactivity) holds the selection; a watcher drops IDs of deleted documents and defaults to "all" on first load. The scope summary ("2 of 3 documents in scope") is computed from the same state.

### Why it matters
Scoping is the user's precision tool: single-document questions get single-document evidence. Because the backend enforces it in SQL, the UI can't leak cross-document passages even if it tried.

---

## Byte 3 — Cited-only sources

### Builds on
Byte 1, [API](../backend/api.md) (Byte 5: ranks).

### In plain terms
The backend sends all retrieved candidates up front, but the Sources panel must show only passages the answer actually cited. `onDone` parses `[n]` markers from the final answer text and drops uncited sources — so the panel always matches the emitted citations exactly.

### Relevant code
`frontend/src/utils/format.js`:

```js
export function citedRanks(text) {
  const ranks = new Set();
  const re = /\[(\d+)\]/g;
  let m;
  while ((m = re.exec(text)) !== null) ranks.add(Number(m[1]));
  return ranks;
}
export function filterSourcesToCited(sources, answerText) {
  const cited = citedRanks(answerText);
  return (sources || []).filter(s => cited.has(s.rank));
}
```

### What's happening
A regex extracts every `[n]` marker (deduped via `Set`); sources whose `rank` wasn't cited are filtered out. Declined answers clear sources entirely. The per-message `[n]` chips and the Sources panel both read the same filtered array, so they can't disagree. Clicking a citation scrolls the corresponding source card into view.

### Why it matters
Retrieval returns *candidates*; citations mark *evidence*. This filter is what makes the UI's claim "these passages support this answer" literally true. Markdown rendering (`renderMarkdown`) and click-to-source binding (`bindCitations`) live in `utils/markdown.js`.

---

## Byte 4 — Conversations: persist, restore, continue

### Builds on
Byte 1, [Composables](./composables.md) (`useChatHistory`).

### In plain terms
After each answer, `persistCurrent()` upserts the conversation (messages + `scopeIds`) to the shared history store; `openConversation()` (from the sidebar) saves the current chat then loads another, restoring its scope; `newChat()` saves and blanks. `onMounted` restores the in-progress chat after refresh.

### Relevant code
```js
function persistCurrent() {
  if (!messages.value.length) return;
  if (!currentConvoId.value) currentConvoId.value = 'c' + Date.now();
  const existing = conversations.value.find(c => c.id === currentConvoId.value);
  const title = existing?.title || (firstUser ? firstUser.content.slice(0, 60) : 'Conversation');
  saveConversation({ id: currentConvoId.value, title, at: Date.now(),
                     scopeIds: scopeIdsOrNull(), messages: snapshotMessages() });
}
```

### What's happening
The title is derived from the first question only for new chats — a user rename is preserved because `existing?.title` wins. `scopeIds` (`null` = all documents) is restored on open, filtered to documents that still exist. `App.vue` drives `newChat`/`openConversation`/`deleteConversation` through `defineExpose`'d methods when the sidebar requests them.

### Why it matters
History is local-first and lossless: every Q&A survives refresh, navigation, and renames, with its evidence attached. The sidebar (`AppSidebar.vue`) is just a view over this same store — see [Frontend Architecture](./architecture.md) Byte 3.

---

## Putting It Together

`NotebookView` orchestrates the read path: scope selection → `streamChat` → token streaming → cited-only sources → persistence. It trusts the backend for grounding (threshold, `[DECLINED]`) and adds the final UI-level guarantee (cited-only panel). Next: [Composables](./composables.md) for the shared state behind it all.
