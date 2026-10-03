<template>
  <!-- grid card -->
  <article v-if="layout === 'grid'" class="vb-card vb-doc-card" :class="{ processing: doc.status === 'processing' }">
    <div class="vb-doc-top">
      <div class="vb-doc-thumb" :class="doc.status">
        <VbIcon name="file" :size="26" />
      </div>
      <div class="vb-doc-actions">
        <button
          class="vb-icon-btn" :class="{ active: isFav(doc.id) }"
          @click.stop="$emit('toggle-fav', doc)"
          :aria-label="isFav(doc.id) ? 'Remove from favorites' : 'Add to favorites'"
          :title="isFav(doc.id) ? 'Remove from favorites' : 'Add to favorites'"
        ><VbIcon name="star" :size="16" /></button>
        <button class="vb-icon-btn" @click.stop="$emit('delete', doc)" aria-label="Delete document" title="Delete">
          <VbIcon name="trash" :size="16" />
        </button>
      </div>
    </div>
    <h3 class="vb-doc-name" :title="doc.filename">{{ doc.filename }}</h3>
    <div class="vb-doc-meta">
      <span v-if="doc.page_count">{{ doc.page_count }} pages</span>
      <span>{{ formatBytes(doc.file_size) }}</span>
    </div>
    <div class="vb-doc-foot">
      <span class="vb-chip" :class="statusChip(doc.status)">
        <span v-if="doc.status === 'processing'" class="vb-dot-pulse" />
        {{ statusLabel(doc.status) }}
      </span>
      <span class="vb-doc-date">{{ timeAgo(doc.created_at) }}</span>
    </div>
    <button v-if="doc.status === 'ready'" class="vb-doc-open" @click="$emit('open', doc)">
      Open in Notebook <VbIcon name="chevRight" :size="14" />
    </button>
  </article>

  <!-- list row -->
  <article v-else class="vb-doc-row" :class="{ processing: doc.status === 'processing' }">
    <div class="vb-doc-thumb vb-doc-thumb-sm" :class="doc.status">
      <VbIcon name="file" :size="20" />
    </div>
    <div class="vb-doc-row-main">
      <h3 class="vb-doc-name" :title="doc.filename">{{ doc.filename }}</h3>
      <div class="vb-doc-meta">
        <span v-if="doc.page_count">{{ doc.page_count }} pages</span>
        <span>{{ formatBytes(doc.file_size) }}</span>
        <span>{{ formatDate(doc.created_at) }}</span>
        <span v-if="doc.chunk_count">{{ formatNumber(doc.chunk_count) }} chunks</span>
      </div>
    </div>
    <span class="vb-chip" :class="statusChip(doc.status)">
      <span v-if="doc.status === 'processing'" class="vb-dot-pulse" />
      {{ statusLabel(doc.status) }}
    </span>
    <div class="vb-doc-row-actions">
      <button class="vb-icon-btn" :class="{ active: isFav(doc.id) }" @click="$emit('toggle-fav', doc)"
        :aria-label="isFav(doc.id) ? 'Remove from favorites' : 'Add to favorites'">
        <VbIcon name="star" :size="16" />
      </button>
      <button v-if="doc.status === 'ready'" class="vb-btn vb-btn-soft vb-btn-sm" @click="$emit('open', doc)">Open</button>
      <button class="vb-icon-btn vb-icon-btn-danger" @click="$emit('delete', doc)" aria-label="Delete document">
        <VbIcon name="trash" :size="16" />
      </button>
    </div>
  </article>
</template>

<script setup>
import VbIcon from './VbIcon.vue';
import { formatBytes, formatNumber, timeAgo, formatDate } from '../utils/format.js';
import { useFavorites } from '../composables/usePrefs.js';

defineProps({
  doc: { type: Object, required: true },
  layout: { type: String, default: 'grid' }, // grid | list
});
defineEmits(['open', 'delete', 'toggle-fav']);

const { isFav } = useFavorites();

function statusLabel(s) {
  return s === 'ready' ? 'Ready' : s === 'processing' ? 'Indexing…' : s === 'failed' ? 'Failed' : s;
}
function statusChip(s) {
  return s === 'ready' ? 'vb-chip-success' : s === 'processing' ? 'vb-chip-info' : s === 'failed' ? 'vb-chip-danger' : '';
}
</script>

<style scoped>
.vb-doc-card { padding: 18px; display: flex; flex-direction: column; gap: 0; transition: transform var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out); }
.vb-doc-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.vb-doc-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.vb-doc-thumb {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent-soft); color: var(--accent);
}
.vb-doc-thumb.processing { background: var(--info-soft); color: var(--info); }
.vb-doc-thumb.failed { background: var(--danger-soft); color: var(--danger); }
.vb-doc-thumb-sm { width: 44px; height: 44px; border-radius: 12px; }
.vb-doc-actions { display: flex; gap: 4px; }
.vb-doc-name { font-size: 14.5px; font-weight: 600; margin: 0 0 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; letter-spacing: -0.01em; }
.vb-doc-meta { display: flex; gap: 10px; font-size: 12.5px; color: var(--text-3); margin-bottom: 14px; }
.vb-doc-foot { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 4px; }
.vb-doc-date { font-size: 12px; color: var(--text-3); }
.vb-doc-open {
  margin-top: 12px; padding-top: 12px; border: 0; border-top: 1px solid var(--border);
  background: none; cursor: pointer; width: 100%;
  display: flex; align-items: center; justify-content: center; gap: 4px;
  font: 600 13px var(--font-sans); color: var(--accent);
}
.vb-doc-open:hover { color: var(--accent-strong); }

.vb-doc-row {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius-md);
  transition: box-shadow var(--dur-fast), border-color var(--dur-fast);
}
.vb-doc-row:hover { border-color: var(--border-strong); box-shadow: var(--shadow-sm); }
.vb-doc-row-main { flex: 1; min-width: 0; }
.vb-doc-row .vb-doc-name { margin-bottom: 4px; }
.vb-doc-row .vb-doc-meta { margin-bottom: 0; flex-wrap: wrap; }
.vb-doc-row-actions { display: flex; align-items: center; gap: 6px; }

.vb-icon-btn {
  width: 32px; height: 32px; border-radius: 9px; border: 0;
  display: inline-flex; align-items: center; justify-content: center;
  background: transparent; color: var(--text-3); cursor: pointer;
  transition: background var(--dur-fast), color var(--dur-fast);
}
.vb-icon-btn:hover { background: var(--hover-bg); color: var(--text-1); }
.vb-icon-btn.active { color: var(--warning); }
.vb-icon-btn.active svg { fill: currentColor; }
.vb-icon-btn-danger:hover { background: var(--danger-soft); color: var(--danger); }

.vb-dot-pulse { width: 7px; height: 7px; border-radius: 50%; background: currentColor; animation: vb-pulse-dot 1.2s ease-in-out infinite; }
</style>
