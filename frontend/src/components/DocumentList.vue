<template>
  <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
    <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3">
      <h2 class="font-semibold text-slate-800">Library</h2>
      <span class="text-xs text-slate-500">{{ documents.length }} document{{ documents.length === 1 ? '' : 's' }}</span>
    </div>
    <div v-if="!documents.length" class="px-5 py-10 text-center text-sm text-slate-500">
      No PDFs yet. Upload your study material above — Vector-Brain will parse,
      chunk and index it for semantic search.
    </div>
    <ul v-else class="divide-y divide-slate-100">
      <li v-for="d in documents" :key="d.id" class="flex items-center gap-3 px-5 py-3">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-lg">📕</div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-slate-800" :title="d.filename">{{ d.filename }}</p>
          <p class="text-xs text-slate-500">
            <span v-if="d.status === 'ready'">{{ d.chunk_count }} chunks · {{ d.page_count }} pages · {{ fmtSize(d.file_size) }}</span>
            <span v-else-if="d.status === 'processing'" class="text-amber-600">Parsing & indexing…</span>
            <span v-else class="text-red-600">Failed: {{ d.error }}</span>
          </p>
        </div>
        <span
          class="rounded-full px-2.5 py-0.5 text-xs font-medium"
          :class="d.status === 'ready' ? 'bg-emerald-100 text-emerald-700' : d.status === 'processing' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'"
        >{{ d.status }}</span>
        <button
          @click="$emit('delete', d)"
          class="rounded-lg px-2 py-1 text-sm text-slate-400 hover:bg-red-50 hover:text-red-600"
          title="Delete document"
        >✕</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({ documents: { type: Array, default: () => [] } });
defineEmits(['delete']);

function fmtSize(bytes) {
  if (bytes == null) return '';
  const mb = bytes / 1024 / 1024;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
</script>
