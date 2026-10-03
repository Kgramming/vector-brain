<template>
  <div class="min-h-screen bg-[#f6f4ee] text-slate-800">
    <header class="border-b border-amber-200/60 bg-white/70 backdrop-blur">
      <div class="mx-auto flex max-w-6xl items-center gap-3 px-5 py-4">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-xl text-white">🧠</div>
        <div>
          <h1 class="text-lg font-bold tracking-tight">Vector-Brain</h1>
          <p class="text-xs text-slate-500">Notebook LLM Lite — your second brain for studying</p>
        </div>
        <nav class="ml-auto flex gap-1 rounded-xl bg-slate-100 p-1">
          <button
            v-for="t in tabs" :key="t.id"
            @click="tab = t.id"
            class="rounded-lg px-4 py-1.5 text-sm font-medium transition-colors"
            :class="tab === t.id ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
          >{{ t.label }}</button>
        </nav>
        <button
          @click="kbOpen = true"
          class="rounded-xl bg-amber-400 px-4 py-2 text-sm font-semibold text-amber-950 hover:bg-amber-300"
          title="Explain code or technical content in 10-second Knowledge Bytes"
        >⚡ Knowledge Bytes</button>
      </div>
    </header>

    <div v-if="health && health.groq_mode === 'mock'" class="bg-amber-100 px-5 py-1.5 text-center text-xs text-amber-800">
      Running in <b>mock mode</b> — set <code>GROQ_API_KEY</code> in <code>backend/.env</code> for real answers.
    </div>

    <main class="mx-auto max-w-6xl px-5 py-6">
      <!-- Library tab -->
      <div v-show="tab === 'library'" class="space-y-5">
        <UploadPanel :max-mb="50" @uploaded="onUploaded" />
        <DocumentList :documents="documents" @delete="onDelete" />
      </div>

      <!-- Notebook tab -->
      <div v-show="tab === 'notebook'" class="h-[calc(100vh-220px)] min-h-[480px]">
        <ChatPanel />
      </div>
    </main>

    <footer class="mx-auto max-w-6xl px-5 pb-6 text-center text-xs text-slate-400">
      PDFs → Docling → 384-dim embeddings → PostgreSQL + pgvector → Groq → answers with citations
    </footer>

    <KnowledgeBytesModal :open="kbOpen" @close="kbOpen = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import UploadPanel from './components/UploadPanel.vue';
import DocumentList from './components/DocumentList.vue';
import ChatPanel from './components/ChatPanel.vue';
import KnowledgeBytesModal from './components/KnowledgeBytesModal.vue';
import { getHealth, listDocuments, deleteDocument } from './services/api.js';

const tabs = [
  { id: 'library', label: '📚 Library' },
  { id: 'notebook', label: '💬 Notebook' },
];
const tab = ref('library');
const documents = ref([]);
const health = ref(null);
const kbOpen = ref(false);
let poller = null;

async function refresh() {
  try {
    const [h, d] = await Promise.all([getHealth(), listDocuments()]);
    health.value = h;
    documents.value = d.documents || [];
  } catch { /* backend may be down; UI stays usable */ }
}

async function onUploaded() {
  tab.value = 'library';
  await refresh();
}

async function onDelete(doc) {
  if (!confirm(`Delete "${doc.filename}" and all its indexed chunks?`)) return;
  await deleteDocument(doc.id);
  await refresh();
}

onMounted(() => {
  refresh();
  // Poll while any document is still being parsed/indexed.
  poller = setInterval(() => {
    if (documents.value.some(d => d.status === 'processing')) refresh();
  }, 3000);
});
onUnmounted(() => clearInterval(poller));
</script>
