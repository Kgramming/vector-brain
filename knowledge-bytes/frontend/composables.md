# Knowledge Bytes: Composables & Utilities

> Source: `frontend/src/composables/usePrefs.js`, `frontend/src/composables/useTheme.js`, `frontend/src/composables/useToasts.js`, `frontend/src/utils/format.js`
>
> Covers:
> - `useChatHistory()` — conversations, rename, shared `currentConvoId`
> - `usePrefs()` / `useProfile()` / `useFavorites()` / `useRecents()`
> - `useTheme()` — theme/accent/density
> - `useToasts()` — transient notifications
> - `format.js` — display helpers + citation parsing

---

## Byte 1 — `useChatHistory()`: the conversation store

### Builds on
[Notebook](./notebook.md) (Byte 4).

### In plain terms
`useChatHistory()` (in `usePrefs.js`) owns the module-level `conversations` ref — the single source of truth for chat history, shared by `NotebookView` and `AppSidebar`. It upserts (newest first, capped at 30), renames in place (no reorder), and removes, persisting everything to `localStorage` under `vb:conversations`.

### Relevant code
```js
const conversations = ref(loadJSON('conversations', []));
const currentConvoId = ref(null);  // shared with the sidebar

export function useChatHistory() {
  function saveConversation(conv) {
    conversations.value = [conv, ...conversations.value.filter(c => c.id !== conv.id)].slice(0, 30);
    saveJSON('conversations', conversations.value);
  }
  function renameConversation(id, title) {
    const idx = conversations.value.findIndex(c => c.id === id);
    if (idx < 0) return;
    const next = [...conversations.value];          // in-place: renaming never reorders
    next[idx] = { ...next[idx], title: (title || '').trim() || next[idx].title };
    conversations.value = next;
    saveJSON('conversations', conversations.value);
  }
  ...
  return { conversations, currentConvoId, saveConversation, renameConversation, removeConversation, clearAll };
}
```

### What's happening
Because the refs live at module scope, every caller shares the same reactive state — no prop drilling, no store library. `saveConversation` unshifts (recent activity first); `renameConversation` deliberately avoids unshifting so renames don't reorder. `currentConvoId` (also module-level) is how the sidebar knows which chat is active.

### Why it matters
This is the pattern for all client state in the app: module-level refs + localStorage + tiny functions. Understand this composable and you understand `useFavorites`, `useRecents`, and `useLibrary` too.

---

## Byte 2 — Preferences, profile, recents

### Builds on
Byte 1 (the composable pattern).

### In plain terms
`usePrefs.js` also hosts `useProfile()` (name/workspace), `useFavorites()` (document IDs), `useRecents()` (recent documents + questions), and `usePrefs()` (notebook settings like `topK`, citation style). All follow the same shape: `loadJSON` on init, `saveJSON` on change, `vb:`-prefixed keys.

### Relevant code
```js
function loadJSON(key, fallback) {
  try { const raw = localStorage.getItem('vb:' + key); return raw ? JSON.parse(raw) : fallback; }
  catch { return fallback; }
}
```

### What's happening
Every piece of UI state that isn't conversation history lives here: theme-adjacent prefs, the question history on Home, favorite documents. The `try/catch` makes corrupted localStorage a non-event (falls back to defaults).

### Why it matters
The backend is stateless per user (no auth, no sessions) — *all* personalization is client-side in these composables. Nothing sensitive is stored: no API keys, no tokens.

---

## Byte 3 — `useTheme()` and `useToasts()`

### Builds on
[Frontend Architecture](./architecture.md) (Byte 4: tokens).

### In plain terms
`useTheme()` (in `useTheme.js`) applies the saved theme/accent/density as `data-*` attributes on `<html>` before first paint and exposes setters used by Settings. `useToasts()` (in `useToasts.js`) provides transient `success`/`error`/`info` notifications rendered by the global `Toasts` component.

### Why it matters
These are the two cross-cutting UI concerns: theming (visual consistency) and toasts (user feedback for async actions like upload errors or "select at least one document"). Both are consumed via the same composable pattern as Byte 1.

---

## Byte 4 — `format.js`: small helpers, one critical parser

### Builds on
[Notebook](./notebook.md) (Byte 3: cited-only sources).

### In plain terms
`utils/format.js` holds display helpers (`shortName`, `pageLabel`, `relevanceLabel`, `formatBytes`, `timeAgo`) — and the citation parser (`citedRanks` / `filterSourcesToCited`) that enforces source/citation consistency. It's pure functions, no Vue, so it's unit-tested directly (`frontend/tests/unit.mjs`).

### Why it matters
Keeping the citation parser in a pure, tested utility (rather than buried in the view) is what makes the grounding guarantee verifiable. The display helpers keep formatting consistent between the Sources panel, chat chips, and Library.

---

## Putting It Together

The frontend's state philosophy: module-level reactive refs, localStorage persistence, and one composable per concern — no Vuex/Pinia, no backend sessions. `useChatHistory` (conversations), `useLibrary` (documents), `usePrefs` (preferences), `useTheme`/`useToasts` (UI chrome). If you need to add client state, follow this pattern.
