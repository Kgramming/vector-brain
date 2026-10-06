# 07 — Frontend Chat and Library

How the UI drives the backend: streaming chat in the Notebook, uploads in the Library, and the composables holding it together.

Source files in this byte: `frontend/src/services/api.js` (`streamChat`), `frontend/src/views/NotebookView.vue` (`send`), `frontend/src/components/UploadModal.vue`, `frontend/src/composables/useLibrary.js`, `frontend/src/composables/usePrefs.js` (`useChatHistory`), `frontend/src/utils/format.js`

---

### Byte 1: `streamChat()` — SSE over fetch

**Builds on:** `04`, `06`

**In plain terms:**
`services/api.js` POSTs the question (plus `top_k` and `document_ids`, or `null` for "all documents") and parses the SSE stream manually with `fetch` + `ReadableStream` — `EventSource` can't do POST bodies. Events dispatch to `onSources` / `onToken` / `onDone` / `onError`.

**The code:**
```js
// frontend/src/services/api.js
body: JSON.stringify({ question, top_k: topK ?? null,
                       document_ids: documentIds?.length ? documentIds : null })
```

---

### Byte 2: `NotebookView.send()` — one question, end to end

**Builds on:** Byte 1

**In plain terms:**
`send()` pushes the user message, appends an empty assistant message, and streams into it: `onSources` fills the Sources panel, `onToken` appends Markdown-rendered text, `onDone` filters sources to exactly the `[n]` ranks the answer cited (`filterSourcesToCited`), marks declined, and persists the conversation. The document-scope checkboxes become `document_ids` — enforced server-side in SQL.

**The code:**
```js
ans.sources = ans.declined ? [] : filterSourcesToCited(ans.sources, ans.content);
```

Retrieval returns *candidates*; citations mark *evidence* — this line is what makes "these passages support this answer" literally true.

---

### Byte 3: Upload with real progress

**Builds on:** `02` (Byte 1)

**In plain terms:**
`UploadModal.vue` uses `XMLHttpRequest` (fetch can't report upload progress) to show real byte progress, then polls document `status` to animate pipeline stages. `409`/`413`/`400` map to friendly messages. `useLibrary()` (in `composables/useLibrary.js`) holds the shared `documents` ref and re-fetches every 2.5 s while anything is `processing` — no websockets needed.

---

### Byte 4: History is a shared composable

**Builds on:** Byte 2, `06` (Byte 3)

**In plain terms:**
`useChatHistory()` (in `usePrefs.js`) owns module-level `conversations` + `currentConvoId` refs, so NotebookView and the sidebar share one reactive store with no prop drilling. `saveConversation` upserts newest-first (cap 30); `renameConversation` edits in place without reordering; everything persists to `localStorage`. `persistCurrent()` runs after each answer and preserves user-renamed titles.

**The code:**
```js
// module scope = shared by every caller
const conversations = ref(loadJSON('conversations', []));
const currentConvoId = ref(null);
```

---

## PUTTING IT TOGETHER

`api.js` is the only file that touches HTTP; views call it and render. Notebook streams answers into reactive messages with cited-only sources; the Library polls ingestion status; composables hold all client state in localStorage. The backend never keeps per-user state — refresh the page and the UI rebuilds itself from storage plus one `GET /api/documents`.
