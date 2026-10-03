<template>
  <div class="vb-library">
    <div class="vb-lib-head vb-rise">
      <div>
        <h1>Library</h1>
        <p>{{ documents.length }} document{{ documents.length === 1 ? '' : 's' }} · {{ formatNumber(totalPages) }} pages · {{ formatNumber(totalChunks) }} chunks</p>
      </div>
      <button class="vb-btn vb-btn-primary" @click="$emit('upload')">
        <VbIcon name="upload" :size="16" /> Upload PDF
      </button>
    </div>

    <!-- toolbar -->
    <div class="vb-toolbar vb-card">
      <div class="vb-search">
        <VbIcon name="search" :size="16" />
        <input
          v-model="query" type="search" placeholder="Search documents…"
          aria-label="Search documents" class="vb-search-input"
        />
      </div>
      <div class="vb-toolbar-actions">
        <select v-model="statusFilter" class="vb-select vb-select-sm" aria-label="Filter by status">
          <option value="all">All statuses</option>
          <option value="ready">Ready</option>
          <option value="processing">Indexing</option>
          <option value="failed">Failed</option>
        </select>
        <select v-model="sortBy" class="vb-select vb-select-sm" aria-label="Sort documents">
          <option value="recent">Recently added</option>
          <option value="name">Name</option>
          <option value="size">Size</option>
          <option value="pages">Pages</option>
        </select>
        <div class="vb-view-toggle" role="group" aria-label="View mode">
          <button :class="{ active: viewMode === 'grid' }" @click="setView('grid')" title="Grid view" aria-label="Grid view">
            <VbIcon name="grid" :size="16" />
          </button>
          <button :class="{ active: viewMode === 'list' }" @click="setView('list')" title="List view" aria-label="List view">
            <VbIcon name="list" :size="16" />
          </button>
        </div>
      </div>
    </div>

    <!-- content -->
    <div v-if="loading" :class="viewMode === 'grid' ? 'vb-doc-grid' : 'vb-doc-list'">
      <div v-for="i in 6" :key="i" class="vb-skeleton" :style="{ height: viewMode === 'grid' ? '210px' : '72px' }" />
    </div>

    <EmptyState
      v-else-if="!documents.length"
      icon="library" title="No documents yet"
      description="Upload PDFs to build your research library. They'll be parsed, chunked, and indexed for semantic search."
    >
      <template #actions>
        <button class="vb-btn vb-btn-primary" @click="$emit('upload')"><VbIcon name="upload" :size="16" /> Upload PDF</button>
      </template>
    </EmptyState>

    <EmptyState
      v-else-if="!filtered.length"
      icon="search" title="No matches"
      description="Try a different search term or clear the filters."
      compact
    >
      <template #actions>
        <button class="vb-btn vb-btn-secondary vb-btn-sm" @click="query = ''; statusFilter = 'all'">Clear filters</button>
      </template>
    </EmptyState>

    <div v-else :class="viewMode === 'grid' ? 'vb-doc-grid' : 'vb-doc-list'">
      <DocCard
        v-for="d in filtered" :key="d.id" :doc="d" :layout="viewMode"
        @open="$emit('open-doc', $event)" @delete="askDelete($event)" @toggle-fav="$emit('toggle-fav', $event)"
      />
    </div>

    <!-- delete confirm -->
    <div v-if="deleting" class="vb-modal-backdrop" @click.self="deleting = null" role="dialog" aria-modal="true" aria-label="Confirm delete">
      <div class="vb-modal vb-confirm">
        <h3>Delete document?</h3>
        <p>“{{ deleting.filename }}” and all its {{ formatNumber(deleting.chunk_count || 0) }} indexed chunks will be permanently removed.</p>
        <div class="vb-confirm-actions">
          <button class="vb-btn vb-btn-secondary" @click="deleting = null">Cancel</button>
          <button class="vb-btn vb-btn-danger" @click="confirmDelete" :disabled="deletingBusy">
            {{ deletingBusy ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import VbIcon from '../components/VbIcon.vue';
import EmptyState from '../components/EmptyState.vue';
import DocCard from '../components/DocCard.vue';
import { formatNumber } from '../utils/format.js';
import { deleteDocument } from '../services/api.js';
import { usePrefs } from '../composables/usePrefs.js';
import { useToasts } from '../composables/useToasts.js';

const props = defineProps({
  documents: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  totalPages: { type: Number, default: 0 },
  totalChunks: { type: Number, default: 0 },
});
const emit = defineEmits(['upload', 'open-doc', 'toggle-fav', 'refresh']);

const { libraryPrefs, saveLibrary } = usePrefs();
const { success, error: toastError } = useToasts();

const query = ref('');
const statusFilter = ref('all');
const sortBy = ref(libraryPrefs.value.sort || 'recent');
const viewMode = ref(libraryPrefs.value.view || 'grid');
const deleting = ref(null);
const deletingBusy = ref(false);

function setView(v) {
  viewMode.value = v;
  saveLibrary({ view: v });
}

const filtered = computed(() => {
  let docs = props.documents.slice();
  if (statusFilter.value !== 'all') docs = docs.filter(d => d.status === statusFilter.value);
  const q = query.value.trim().toLowerCase();
  if (q) docs = docs.filter(d => (d.filename || '').toLowerCase().includes(q));
  const by = {
    recent: (a, b) => new Date(b.created_at) - new Date(a.created_at),
    name: (a, b) => (a.filename || '').localeCompare(b.filename || ''),
    size: (a, b) => (b.file_size || 0) - (a.file_size || 0),
    pages: (a, b) => (b.page_count || 0) - (a.page_count || 0),
  }[sortBy.value];
  docs.sort(by);
  return docs;
});

function askDelete(doc) { deleting.value = doc; }

async function confirmDelete() {
  if (!deleting.value) return;
  deletingBusy.value = true;
  try {
    await deleteDocument(deleting.value.id);
    success(`Deleted "${deleting.value.filename}".`);
    deleting.value = null;
    emit('refresh');
  } catch (e) {
    toastError(e.message || 'Delete failed.');
  } finally {
    deletingBusy.value = false;
  }
}
</script>

<style scoped>
.vb-library { max-width: 1120px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
.vb-lib-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.vb-lib-head h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px; }
.vb-lib-head p { font-size: 13.5px; color: var(--text-2); margin: 0; }

.vb-toolbar {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  flex-wrap: wrap;
}
.vb-search {
  flex: 1; min-width: 200px; display: flex; align-items: center; gap: 8px;
  background: var(--input-bg); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 0 12px; color: var(--text-3);
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.vb-search:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.vb-search-input { border: 0; background: none; outline: none; flex: 1; padding: 9px 0; font-size: 13.5px; color: var(--text-1); }
.vb-search-input::placeholder { color: var(--text-3); }
.vb-toolbar-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.vb-select-sm { width: auto; padding: 8px 10px; font-size: 13px; }
.vb-view-toggle {
  display: flex; background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 3px; gap: 2px;
}
.vb-view-toggle button {
  border: 0; background: none; cursor: pointer; padding: 7px 9px; border-radius: 7px;
  color: var(--text-3); display: inline-flex;
}
.vb-view-toggle button.active { background: var(--surface); color: var(--accent); box-shadow: var(--shadow-sm); }

.vb-doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.vb-doc-list { display: flex; flex-direction: column; gap: 10px; }

.vb-confirm { max-width: 420px; padding: 24px; }
.vb-confirm h3 { margin: 0 0 8px; font-size: 17px; font-weight: 700; }
.vb-confirm p { margin: 0 0 20px; font-size: 13.5px; color: var(--text-2); line-height: 1.6; }
.vb-confirm-actions { display: flex; justify-content: flex-end; gap: 10px; }

@media (max-width: 640px) {
  .vb-lib-head { flex-direction: column; }
  .vb-toolbar-actions { width: 100%; }
  .vb-select-sm { flex: 1; }
}
</style>
