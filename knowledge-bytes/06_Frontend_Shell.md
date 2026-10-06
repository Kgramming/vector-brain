# 06 — Frontend Shell

How the Vue app is put together: no router, a view-switching shell, a sidebar that doubles as the conversation manager, and token-based theming.

Source files in this byte: `frontend/src/main.js`, `frontend/src/App.vue`, `frontend/src/components/AppSidebar.vue`, `frontend/src/styles/tokens.css`, `frontend/src/composables/useTheme.js`

---

### Byte 1: Boot without a flash

**Builds on:** `01` (Byte 4)

**In plain terms:**
`main.js` applies the persisted theme *before* Vue mounts, then mounts `App`. Three lines, and the first paint already has the right colors.

**The code:**
```js
// frontend/src/main.js
useTheme().apply()              // reads localStorage, sets data-theme on <html>
createApp(App).mount('#app')
```

---

### Byte 2: `App.vue` switches views, wires everything

**Builds on:** Byte 1

**In plain terms:**
`App.vue` holds a `view` ref and renders the matching component with `v-if` — leaving Notebook unmounts it (its state was already persisted). It's also the only component talking to *both* sidebar and views: sidebar chat events (`new-chat`, `open-chat`, `delete-chat`) call exposed NotebookView methods through a template ref, navigating there first if needed.

**The code:**
```text
AppSidebar ──events──→ App.vue ──notebookRef.newChat()/openConversation()──→ NotebookView
     ↑                                                                    (mounted via v-if)
upload events ──→ UploadModal (global) ──@uploaded──→ refresh() ──→ useLibrary
```

---

### Byte 3: The sidebar is the conversation manager

**Builds on:** Byte 2

**In plain terms:**
`AppSidebar.vue` renders nav (Home/Library/Notebook/Favorites/Recent), the Workspace section, then **+ New chat** and the **Recent chats** list (newest first) in the flexible middle — the list scrolls independently without pushing Settings/Profile off. Each chat has a hover `…` menu (Rename inline, Delete with confirm) and the active chat is highlighted. It reads the shared `useChatHistory()` store directly, so it can never disagree with the Notebook.

---

### Byte 4: Theming is just CSS variables

**Builds on:** Byte 1

**In plain terms:**
`styles/tokens.css` defines every color/spacing token; themes are `data-theme` attribute selectors reassigning them. Components never hard-code colors — which is why Light/Dark/Midnight/High-Contrast all work with zero runtime cost.

---

## PUTTING IT TOGETHER

A shell (`App.vue`) around focused views, navigation as a ref, conversations managed from the sidebar, styling as tokens. All client state lives in composables + localStorage — the backend stays stateless. `07` covers the views that do the work.
