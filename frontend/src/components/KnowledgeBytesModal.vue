<template>
  <div class="vb-modal-backdrop" @click.self="$emit('close')" role="dialog" aria-modal="true" aria-label="Knowledge Bytes explainer">
    <div class="vb-modal vb-kb-modal">
      <div class="vb-kb-head">
        <div>
          <h2>Knowledge Bytes</h2>
          <p>Paste code or technical text — get architecture-first 10-second explainers.</p>
        </div>
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="$emit('close')" aria-label="Close">
          <VbIcon name="x" :size="18" />
        </button>
      </div>

      <div class="vb-kb-body">
        <label class="vb-label" for="kb-content">Content to explain</label>
        <textarea
          id="kb-content" v-model="content" rows="6"
          placeholder="Paste code, a config file, an error trace, or any technical content…"
          class="vb-textarea vb-kb-mono"
        ></textarea>
        <div class="vb-kb-row">
          <div>
            <label class="vb-label" for="kb-lang">Language <span class="vb-optional">(optional)</span></label>
            <input id="kb-lang" v-model="language" placeholder="e.g. python" class="vb-input" />
          </div>
          <div>
            <label class="vb-label" for="kb-ctx">Context <span class="vb-optional">(optional)</span></label>
            <input id="kb-ctx" v-model="contextNote" placeholder="e.g. auth module" class="vb-input" />
          </div>
        </div>
        <p v-if="error" class="vb-kb-error" role="alert">{{ error }}</p>
        <div v-if="result || busy" class="vb-kb-result">
          <pre>{{ result }}<span v-if="busy" class="vb-caret" /></pre>
        </div>
      </div>

      <div class="vb-kb-foot">
        <button class="vb-btn vb-btn-secondary" @click="$emit('close')">Close</button>
        <button class="vb-btn vb-btn-primary" @click="generate" :disabled="busy || !content.trim()">
          <VbIcon name="zap" :size="15" /> {{ busy ? 'Explaining…' : 'Generate Bytes' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import VbIcon from './VbIcon.vue';
import { streamKnowledgeBytes } from '../services/api.js';

defineEmits(['close']);

const content = ref('');
const language = ref('');
const contextNote = ref('');
const result = ref('');
const busy = ref(false);
const error = ref('');

async function generate() {
  error.value = '';
  result.value = '';
  busy.value = true;
  try {
    await streamKnowledgeBytes(
      { content: content.value, language: language.value, context_note: contextNote.value },
      {
        onToken: (t) => { result.value += t; },
        onDone: () => { busy.value = false; },
        onError: (e) => { throw e; },
      }
    );
  } catch (e) {
    error.value = e.message || 'Generation failed';
    busy.value = false;
  }
}
</script>

<style scoped>
.vb-kb-modal { max-width: 640px; max-height: 88vh; display: flex; flex-direction: column; }
.vb-kb-head { display: flex; align-items: flex-start; justify-content: space-between; padding: 22px 22px 0; }
.vb-kb-head h2 { margin: 0 0 4px; font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }
.vb-kb-head p { margin: 0; font-size: 13px; color: var(--text-2); }
.vb-kb-body { padding: 18px 22px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.vb-kb-mono { font-family: var(--font-mono); font-size: 12.5px; }
.vb-kb-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.vb-optional { font-weight: 400; color: var(--text-3); }
.vb-kb-error {
  margin: 0; padding: 10px 12px; border-radius: var(--radius-md);
  background: var(--danger-soft); color: var(--danger); font-size: 13px;
}
.vb-kb-result {
  background: var(--bg-soft); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 14px 16px; max-height: 320px; overflow-y: auto;
}
.vb-kb-result pre {
  margin: 0; white-space: pre-wrap; font: 400 12.5px/1.7 var(--font-mono); color: var(--text-1);
}
.vb-caret {
  display: inline-block; width: 8px; height: 15px; margin-left: 3px;
  background: var(--accent); border-radius: 2px; vertical-align: -2px;
  animation: vb-pulse-dot 1s ease-in-out infinite;
}
.vb-kb-foot { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 22px 20px; border-top: 1px solid var(--border); }
@media (max-width: 560px) { .vb-kb-row { grid-template-columns: 1fr; } }
</style>
