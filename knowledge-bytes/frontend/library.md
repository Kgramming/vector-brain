# Knowledge Bytes: Library & Upload

> Source: `frontend/src/views/LibraryView.vue`, `frontend/src/components/UploadModal.vue`, `frontend/src/composables/useLibrary.js`, `frontend/src/components/DocCard.vue`
>
> Covers:
> - `useLibrary()` — shared document state + ingestion polling
> - `UploadModal` — XHR upload with real progress, staged pipeline display
> - `LibraryView` / `DocCard` — document management UI

---

## Byte 1 — `useLibrary()`: one shared document store

### Builds on
[Services](./services.md) (Byte 1).

### In plain terms
`useLibrary()` holds the module-level `documents` ref that every view reads. `refresh()` fetches health + documents together; `startPolling()` re-fetches every 2.5 s while any document is still `processing`, so ingestion progress appears live with no websockets.

### Relevant code
`frontend/src/composables/useLibrary.js`:

```js
async function refresh() {
  try {
    const [h, d] = await Promise.all([getHealth(), listDocuments()]);
    health.value = h;
    documents.value = (d.documents || []).slice().sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    backendDown.value = false;
  } catch { backendDown.value = true; }
}

function startPolling() {
  stopPolling();
  poller = setInterval(() => {
    if (documents.value.some(d => d.status === 'processing')) refresh();
  }, 2500);
}
```

### What's happening
Documents are sorted newest-first on every refresh. Polling is conditional — the interval only fires `refresh()` when something is actually ingesting, so an idle library costs nothing. `backendDown` drives the red banner in `App.vue`. Derived computeds (`readyDocs`, `totalPages`, `totalChunks`) feed the sidebar badges and the Home dashboard.

### Why it matters
Because the ref is module-level, `LibraryView`, `HomeView`, and `NotebookView` always see the same list without prop drilling or a store library. The `processing → ready` transition from [Ingestion](../backend/ingest.md) surfaces here as a live UI update.

---

## Byte 2 — `UploadModal`: real progress, staged pipeline

### Builds on
Byte 1, [API](../backend/api.md) (Byte 2: the upload endpoint).

### In plain terms
`UploadModal.vue` uploads each PDF with `XMLHttpRequest` (not `fetch`) so it can report real byte progress, then polls the document's status to animate it through pipeline stages (uploaded → parsed → chunked → embedded → indexed).

### Relevant code
```js
/** Upload with real progress via XHR, then poll for ingestion stages. */
const xhr = new XMLHttpRequest();
...
xhr.upload.onprogress = (e) => {
  if (e.lengthComputable) entry.progress = Math.round((e.loaded / e.total) * 100);
};
```

### What's happening
`fetch()` can't report upload progress, hence XHR. Each file is a state machine (`queued → uploading → processing → ready|failed`) rendered as a row with a progress bar and stage dots. HTTP errors map to UI states: `409` shows "already in your library", `413` the size limit, `400` the PDF-only rule. On success it emits `uploaded`, and `App.vue` calls `refresh()`.

### Why it matters
The modal is the write path's frontend face: it turns the backend's `202 + background task` contract into something a user can watch. The stage display is client-side inference from `status` polling — the backend doesn't push stage events.

---

## Byte 3 — `LibraryView` / `DocCard`: managing documents

### Builds on
Byte 1.

### In plain terms
`LibraryView.vue` renders the document grid/list with search, sort, and filters; `DocCard.vue` renders one document (status badge, page/chunk counts, favorite star, actions). Delete calls `deleteDocument(id)` then `refresh()`; "Open in Notebook" emits `open-doc`, which `App.vue` turns into a scoped Notebook session.

### What's happening
All actions are thin: the view calls an `api.js` function and refreshes the shared store. Favorites are local-only (`useFavorites` in `usePrefs.js` — a list of document IDs in localStorage). The status badge (`processing`/`ready`/`failed`) is the direct visualization of the `documents.status` column from [Database](../backend/db.md).

### Why it matters
The Library is deliberately dumb — no local caching, no optimistic updates beyond the upload modal. The server (via `useLibrary`) is the source of truth, which keeps the UI consistent with ingestion reality.

---

## Putting It Together

Upload (`UploadModal` → XHR → `202`), track (`useLibrary` polling → `documents` ref), manage (`LibraryView`/`DocCard` → API → refresh). The frontend never guesses ingestion state — it polls the same `status` column the pipeline writes. Next: [Notebook](./notebook.md), where documents become answers.
