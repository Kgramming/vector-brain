# Knowledge Bytes: Frontend Architecture

> Source: `frontend/src/main.js`, `frontend/src/App.vue`, `frontend/src/components/AppSidebar.vue`, `frontend/src/views/`
>
> Covers:
> - App bootstrap and view switching (no router)
> - `App.vue` layout (sidebar, views, upload modal)
> - `AppSidebar.vue` (navigation + conversation list)
> - View components and the design-token system

---

## Byte 1 — No router: a `view` ref switches pages

### Builds on
[System Overview](../architecture/system-overview.md) (Byte 4).

### In plain terms
The frontend has no Vue Router. `App.vue` holds a `view` ref (`'home'` | `'library'` | `'notebook'` | …) and renders the matching view component with `v-if`. Navigation is just assigning the ref.

### Relevant code
`frontend/src/App.vue`:

```js
const view = ref('home');
function go(v) {
  view.value = v;
  if (v !== 'notebook') notebookPreset.value = { docIds: [], question: '' };
}
```

```html
<HomeView v-if="view === 'home'" ... />
<LibraryView v-else-if="view === 'library'" ... />
<NotebookView v-else-if="view === 'notebook'" ref="notebookRef" ... />
```

### What's happening
`go('notebook')` swaps the entire main content. Because views use `v-if` (not `v-show`), leaving Notebook *unmounts* it — its in-progress UI state is discarded, but the conversation was already persisted to localStorage, so `onMounted` restores it on return. `notebookPreset` carries one-shot navigation payloads (e.g. "open this doc in Notebook").

### Why it matters
State that must survive navigation lives in composables/localStorage, never in view components. If you're wondering "where did my chat go when I clicked Library?" — the answer is `useChatHistory` + `onMounted` restore.

---

## Byte 2 — `App.vue`: the shell

### Builds on
Byte 1.

### In plain terms
`App.vue` composes the whole screen: `AppSidebar` (desktop) or a drawer (mobile), the main column (topbar on mobile, banners, the current view), plus global `UploadModal` and `Toasts`. It also owns the library data via `useLibrary()` and passes documents down as props.

### Relevant code
```html
<AppSidebar v-if="!isMobile" :view="view" ... @new-chat="handleNewChat" @open-chat="handleOpenChat" />
...
<main class="vb-content" :key="view">
  <NotebookView v-else-if="view === 'notebook'" ref="notebookRef" :documents="documents" ... />
</main>
<UploadModal v-if="uploadOpen" @close="uploadOpen = false" @uploaded="refresh" />
```

### What's happening
Sidebar events (`new-chat`, `open-chat`, `delete-chat`) are handled here by calling exposed NotebookView methods through a template ref (`notebookRef.value?.newChat()`), navigating to the notebook view first if needed. `UploadModal` is global — any view can emit `upload` to open it, and `@uploaded="refresh"` reloads the library when files land.

### Why it matters
`App.vue` is the only component that talks to *both* the sidebar and the views, which is why cross-cutting actions (start a chat from the sidebar, upload from anywhere) are wired here rather than in the views themselves.

---

## Byte 3 — `AppSidebar`: nav plus conversations

### Builds on
Byte 2.

### In plain terms
`AppSidebar.vue` renders the logo, the main nav (Home/Library/Notebook/Favorites/Recent), the Workspace section, the **Recent chats** list with per-chat `…` menus (Rename/Delete), and pinned Settings/Profile at the bottom. The chat list scrolls independently inside the flexible middle area.

### Relevant code
```html
<div v-if="!collapsed" class="vb-chats">
  <button class="vb-new-chat" @click="$emit('new-chat')">…</button>
  <p class="vb-side-heading">Recent chats</p>
  <div class="vb-chat-list">
    <div v-for="c in conversations" :key="c.id" class="vb-chat-item"
         :class="{ active: c.id === currentConvoId }">
      <button class="vb-chat-open" @click="$emit('open-chat', c)">…</button>
      <button class="vb-chat-menu-btn" @click.stop="menuFor = menuFor === c.id ? null : c.id">…</button>
      …
```

### What's happening
The list reads `conversations` directly from the shared `useChatHistory()` composable — no props needed, since the ref is module-level. Rename is an inline input committing via `renameConversation()`; delete is a two-step inline confirm emitting `delete-chat`. The active chat gets `.active` from the shared `currentConvoId`.

### Why it matters
This is the ChatGPT-style history UI: conversations are always visible, one click restores, hover reveals management. All state mutations go through the same composable the Notebook uses, so the two can never disagree.

---

## Byte 4 — Design tokens: theming without a framework

### Builds on
Byte 2.

### In plain terms
All styling is CSS custom properties in `frontend/src/styles/tokens.css` (`--bg`, `--surface`, `--accent`, `--radius-md`, …). Themes (Light/Dark/Midnight/High-Contrast) are attribute selectors on `<html>` that reassign the tokens; components never hard-code colors.

### Relevant code
`frontend/src/main.js`:

```js
// Apply persisted theme/accent/density before first paint (no flash).
useTheme().apply()
```

### What's happening
`useTheme().apply()` (in `composables/useTheme.js`) reads the saved theme/accent/density from localStorage and sets `data-theme` / `data-accent` attributes *before* Vue mounts, so there's no flash of the wrong theme. Every component's scoped CSS references only tokens.

### Why it matters
Theming is zero-cost at runtime (pure CSS variable swaps) and fully local — no server round-trip, no CSS-in-JS. If you add a component, use tokens or it will break in dark mode.

---

## Putting It Together

The frontend is a view-switching shell (`App.vue`) around focused view components, with shared state in composables and all styling via tokens. The sidebar doubles as the conversation manager; the views (`HomeView`, `LibraryView`, `NotebookView`, …) each own one screen. Next: [Services](./services.md) (how the UI talks HTTP), [Library](./library.md) (documents + upload), [Notebook](./notebook.md) (chat), [Composables](./composables.md) (shared state).
