/**
 * Shared library state: documents, health, refresh + background polling
 * while any document is still being ingested.
 */
import { ref, computed, onUnmounted } from 'vue';
import { getHealth, listDocuments } from '../services/api.js';

const documents = ref([]);
const health = ref(null);
const loading = ref(true);
const backendDown = ref(false);

let poller = null;

async function refresh() {
  try {
    const [h, d] = await Promise.all([getHealth(), listDocuments()]);
    health.value = h;
    documents.value = (d.documents || []).slice().sort(
      (a, b) => new Date(b.created_at) - new Date(a.created_at)
    );
    backendDown.value = false;
  } catch {
    backendDown.value = true;
  } finally {
    loading.value = false;
  }
}

function startPolling() {
  stopPolling();
  poller = setInterval(() => {
    if (documents.value.some(d => d.status === 'processing')) refresh();
  }, 2500);
}
function stopPolling() {
  if (poller) { clearInterval(poller); poller = null; }
}

const readyDocs = computed(() => documents.value.filter(d => d.status === 'ready'));
const processingDocs = computed(() => documents.value.filter(d => d.status === 'processing'));
const totalPages = computed(() => documents.value.reduce((n, d) => n + (d.page_count || 0), 0));
const totalChunks = computed(() => documents.value.reduce((n, d) => n + (d.chunk_count || 0), 0));

export function useLibrary() {
  onUnmounted(stopPolling);
  return {
    documents, health, loading, backendDown,
    readyDocs, processingDocs, totalPages, totalChunks,
    refresh, startPolling, stopPolling,
  };
}
