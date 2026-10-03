<template>
  <div class="vb-modal-backdrop" @click.self="$emit('close')" role="dialog" aria-modal="true" aria-label="Upload documents">
    <div class="vb-modal vb-upload-modal">
      <div class="vb-upload-head">
        <div>
          <h2>Add documents</h2>
          <p>PDFs are parsed with Docling and indexed into PostgreSQL + pgvector.</p>
        </div>
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="$emit('close')" aria-label="Close">
          <VbIcon name="x" :size="18" />
        </button>
      </div>

      <!-- drop zone -->
      <div
        v-if="!files.length"
        class="vb-dropzone"
        :class="{ dragging }"
        @click="pickFiles"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="onDrop"
        role="button" tabindex="0"
        @keydown.enter="pickFiles" @keydown.space.prevent="pickFiles"
        aria-label="Drop PDF files here or click to browse"
      >
        <div class="vb-drop-icon"><VbIcon name="upload" :size="28" /></div>
        <p class="vb-drop-title">Drop your PDFs here</p>
        <p class="vb-drop-sub">or <span class="vb-drop-link">browse files</span> — PDF only, up to {{ maxMb }} MB each</p>
        <input ref="fileInput" type="file" accept=".pdf,application/pdf" multiple hidden @change="onPick" />
      </div>
      <div v-else class="vb-dropzone vb-dropzone-mini" @click="pickFiles" role="button" tabindex="0" @keydown.enter="pickFiles">
        <VbIcon name="plus" :size="16" /><span>Add more PDFs</span>
        <input ref="fileInput" type="file" accept=".pdf,application/pdf" multiple hidden @change="onPick" />
      </div>

      <!-- file pipeline list -->
      <div v-if="files.length" class="vb-file-list">
        <div v-for="f in files" :key="f.key" class="vb-file-row">
          <div class="vb-file-icon" :class="f.state">
            <VbIcon :name="f.state === 'failed' ? 'alert' : f.state === 'ready' ? 'check' : 'file'" :size="20" />
          </div>
          <div class="vb-file-main">
            <div class="vb-file-top">
              <span class="vb-file-name" :title="f.file.name">{{ f.file.name }}</span>
              <span class="vb-file-size">{{ formatBytes(f.file.size) }}</span>
            </div>
            <!-- pipeline stages -->
            <ol class="vb-stages" :aria-label="`Processing stages for ${f.file.name}`">
              <li v-for="(s, si) in stages" :key="s.id"
                  class="vb-stage"
                  :class="{ done: si < f.stageIndex || f.state === 'ready',
                            active: si === f.stageIndex && (f.state === 'uploading' || f.state === 'processing'),
                            failed: f.state === 'failed' && si === f.stageIndex }">
                <span class="vb-stage-dot" />
                <span class="vb-stage-label">{{ s.label }}</span>
              </li>
            </ol>
            <div v-if="f.state === 'uploading'" class="vb-progress">
              <div class="vb-progress-bar" :style="{ width: f.progress + '%' }" />
            </div>
            <p v-if="f.state === 'failed'" class="vb-file-error">{{ f.error }}</p>
            <p v-else-if="f.state === 'ready'" class="vb-file-ready">Indexed and ready — ask away in the Notebook.</p>
            <p v-else-if="f.state === 'duplicate'" class="vb-file-warn">Already in your library — skipped.</p>
          </div>
          <button
            v-if="f.state === 'failed' || f.state === 'duplicate'"
            class="vb-btn vb-btn-ghost vb-btn-icon vb-file-remove"
            @click="removeFile(f.key)" aria-label="Remove file"
          ><VbIcon name="x" :size="15" /></button>
        </div>
      </div>

      <div class="vb-upload-foot">
        <p class="vb-upload-note">Supported: PDF · Max {{ maxMb }} MB per file</p>
        <button class="vb-btn vb-btn-primary" @click="$emit('close')">
          {{ allDone ? 'Done' : 'Close' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import VbIcon from './VbIcon.vue';
import { listDocuments, apiUrl } from '../services/api.js';
import { formatBytes } from '../utils/format.js';
import { useToasts } from '../composables/useToasts.js';

const props = defineProps({
  maxMb: { type: Number, default: 50 },
});
const emit = defineEmits(['close', 'uploaded']);

const { error: toastError, success: toastSuccess } = useToasts();

// Pipeline mirrors backend/app/pipeline.py: parse → chunk → embed → index.
const stages = [
  { id: 'upload', label: 'Uploading' },
  { id: 'parse', label: 'Parsing with Docling' },
  { id: 'chunk', label: 'Creating chunks' },
  { id: 'embed', label: 'Generating embeddings' },
  { id: 'index', label: 'Indexing in PostgreSQL' },
  { id: 'ready', label: 'Ready' },
];

const files = ref([]); // {key, file, state, progress, stageIndex, error, docId}
const dragging = ref(false);
const fileInput = ref(null);
let keySeq = 1;
let pollTimer = null;

const allDone = computed(() =>
  files.value.length > 0 &&
  files.value.every(f => ['ready', 'failed', 'duplicate'].includes(f.state))
);

function pickFiles() { fileInput.value?.click(); }
function onPick(e) { addFiles([...e.target.files]); e.target.value = ''; }
function onDrop(e) {
  dragging.value = false;
  addFiles([...e.dataTransfer.files]);
}

function addFiles(list) {
  for (const file of list) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toastError(`"${file.name}" is not a PDF — skipped.`);
      continue;
    }
    if (file.size === 0) {
      toastError(`"${file.name}" is empty — skipped.`);
      continue;
    }
    const entry = {
      key: keySeq++, file,
      state: 'queued', progress: 0, stageIndex: 0, error: '', docId: null,
    };
    files.value.push(entry);
    startUpload(entry);
  }
}

function removeFile(key) {
  files.value = files.value.filter(f => f.key !== key);
}

/** Upload with real progress via XHR, then poll for ingestion stages. */
function startUpload(entry) {
  entry.state = 'uploading';
  entry.stageIndex = 0;
  const xhr = new XMLHttpRequest();
  xhr.open('POST', apiUrl('/api/documents'));
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) entry.progress = Math.round((e.loaded / e.total) * 100);
  };
  xhr.onload = () => {
    if (xhr.status === 202) {
      const body = JSON.parse(xhr.responseText);
      entry.docId = body.id;
      entry.state = 'processing';
      entry.stageIndex = 1;
      advanceStages(entry);
      startPolling();
    } else {
      failEntry(entry, xhr);
    }
  };
  xhr.onerror = () => {
    entry.state = 'failed';
    entry.error = 'Network error — is the backend running?';
  };
  const form = new FormData();
  form.append('file', entry.file);
  xhr.send(form);
}

function failEntry(entry, xhr) {
  let detail = 'Upload failed';
  try { detail = JSON.parse(xhr.responseText).detail || detail; } catch { /* ignore */ }
  if (xhr.status === 409) {
    entry.state = 'duplicate';
  } else {
    entry.state = 'failed';
    entry.error = detail;
  }
}

/** Animate through Docling → chunk → embed → index while the backend works. */
function advanceStages(entry) {
  const tick = () => {
    if (entry.state !== 'processing') return;
    // stages 1..4 are backend work; linger on each a bit for readability
    if (entry.stageIndex < 4) {
      entry.stageIndex += 1;
      setTimeout(tick, 1400 + Math.random() * 1200);
    }
    // stage 5 (indexing) waits for the backend to mark the doc ready
  };
  setTimeout(tick, 1200);
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(async () => {
    const processing = files.value.filter(f => f.state === 'processing' && f.docId);
    if (!processing.length) { clearInterval(pollTimer); pollTimer = null; return; }
    try {
      const { documents } = await listDocuments();
      for (const entry of processing) {
        const doc = documents.find(d => String(d.id) === String(entry.docId));
        if (!doc) continue;
        if (doc.status === 'ready') {
          entry.state = 'ready';
          entry.stageIndex = 5;
          toastSuccess(`"${entry.file.name}" is ready.`);
          emit('uploaded');
        } else if (doc.status === 'failed') {
          entry.state = 'failed';
          entry.error = doc.error || 'Processing failed on the server.';
        }
      }
      if (files.value.every(f => f.state !== 'processing')) {
        clearInterval(pollTimer); pollTimer = null;
      }
    } catch { /* keep polling */ }
  }, 2000);
}

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<style scoped>
.vb-upload-modal { max-width: 640px; max-height: 88vh; display: flex; flex-direction: column; }
.vb-upload-head { display: flex; align-items: flex-start; justify-content: space-between; padding: 22px 22px 0; }
.vb-upload-head h2 { margin: 0 0 4px; font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }
.vb-upload-head p { margin: 0; font-size: 13px; color: var(--text-2); }

.vb-dropzone {
  margin: 18px 22px 0; border: 2px dashed var(--border-strong); border-radius: var(--radius-lg);
  padding: 40px 24px; text-align: center; cursor: pointer;
  transition: border-color var(--dur-fast), background var(--dur-fast);
}
.vb-dropzone:hover, .vb-dropzone.dragging { border-color: var(--accent); background: var(--accent-soft); }
.vb-dropzone:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.vb-drop-icon {
  width: 56px; height: 56px; margin: 0 auto 14px; border-radius: 16px;
  background: var(--accent-soft); color: var(--accent);
  display: flex; align-items: center; justify-content: center;
}
.vb-drop-title { font-size: 15px; font-weight: 600; margin: 0 0 6px; }
.vb-drop-sub { font-size: 13px; color: var(--text-2); margin: 0; }
.vb-drop-link { color: var(--accent); font-weight: 600; }
.vb-dropzone-mini {
  margin: 14px 22px 0; padding: 10px; border-style: dashed;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: var(--accent);
}

.vb-file-list { margin: 14px 22px 0; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.vb-file-row {
  display: flex; gap: 12px; padding: 14px;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  background: var(--surface-2);
}
.vb-file-icon {
  width: 40px; height: 40px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-3); color: var(--text-2);
}
.vb-file-icon.ready { background: var(--success-soft); color: var(--success); }
.vb-file-icon.failed { background: var(--danger-soft); color: var(--danger); }
.vb-file-main { flex: 1; min-width: 0; }
.vb-file-top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.vb-file-name { font-size: 13.5px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-file-size { font-size: 12px; color: var(--text-3); flex-shrink: 0; }

.vb-stages { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 12px; }
.vb-stage { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--text-3); }
.vb-stage-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--surface-3); border: 1px solid var(--border-strong); flex-shrink: 0;
}
.vb-stage.done { color: var(--text-2); }
.vb-stage.done .vb-stage-dot { background: var(--success); border-color: var(--success); }
.vb-stage.active { color: var(--accent); font-weight: 600; }
.vb-stage.active .vb-stage-dot { background: var(--accent); border-color: var(--accent); animation: vb-pulse-dot 1.2s ease-in-out infinite; }
.vb-stage.failed { color: var(--danger); font-weight: 600; }
.vb-stage.failed .vb-stage-dot { background: var(--danger); border-color: var(--danger); }

.vb-progress { height: 6px; border-radius: 999px; background: var(--surface-3); margin-top: 10px; overflow: hidden; }
.vb-progress-bar { height: 100%; border-radius: 999px; background: var(--accent); transition: width 0.2s; }
.vb-file-error { margin: 8px 0 0; font-size: 12.5px; color: var(--danger); }
.vb-file-ready { margin: 8px 0 0; font-size: 12.5px; color: var(--success); font-weight: 500; }
.vb-file-warn { margin: 8px 0 0; font-size: 12.5px; color: var(--warning); font-weight: 500; }
.vb-file-remove { align-self: flex-start; }

.vb-upload-foot {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 22px 20px; margin-top: 6px;
}
.vb-upload-note { font-size: 12px; color: var(--text-3); margin: 0; }
</style>
