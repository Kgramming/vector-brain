<template>
  <div
    class="rounded-2xl border-2 border-dashed p-8 text-center transition-colors"
    :class="dragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-white'"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-100 text-2xl">📄</div>
    <p class="font-medium text-slate-800">Drop PDFs here or</p>
    <label class="mt-2 inline-block cursor-pointer rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
      Browse files
      <input type="file" accept="application/pdf,.pdf" multiple class="hidden" @change="onPick" />
    </label>
    <p class="mt-2 text-xs text-slate-500">PDF only · max {{ maxMb }} MB each · duplicate PDFs are skipped</p>
    <p v-if="error" class="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
    <ul v-if="pending.length" class="mt-3 space-y-1 text-left text-sm">
      <li v-for="p in pending" :key="p.name" class="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
        <span class="text-indigo-600">⏳</span>
        <span class="truncate">{{ p.name }}</span>
        <span class="ml-auto text-xs text-slate-500">{{ p.state }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { uploadDocument } from '../services/api.js';

const emit = defineEmits(['uploaded']);
const props = defineProps({ maxMb: { type: Number, default: 50 } });

const dragging = ref(false);
const error = ref('');
const pending = ref([]);

async function handleFiles(files) {
  error.value = '';
  for (const file of files) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      error.value = `"${file.name}" is not a PDF — skipped.`;
      continue;
    }
    const item = { name: file.name, state: 'uploading…' };
    pending.value.push(item);
    try {
      const doc = await uploadDocument(file);
      item.state = 'queued for parsing';
      emit('uploaded', doc);
    } catch (e) {
      if (e.status === 409) item.state = 'already in library';
      else if (e.status === 413) { item.state = 'too large'; error.value = e.message; }
      else { item.state = 'failed'; error.value = e.message; }
    }
  }
  setTimeout(() => { pending.value = pending.value.filter(p => p.state === 'uploading…' || p.state === 'queued for parsing'); }, 4000);
}

function onPick(e) { handleFiles([...e.target.files]); e.target.value = ''; }
function onDrop(e) { dragging.value = false; handleFiles([...e.dataTransfer.files]); }
</script>
