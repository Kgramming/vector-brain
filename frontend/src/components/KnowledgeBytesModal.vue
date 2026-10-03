<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" @click.self="$emit('close')">
    <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl bg-white shadow-xl">
      <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <div>
          <h2 class="font-semibold text-slate-800">Knowledge Bytes</h2>
          <p class="text-xs text-slate-500">Paste code or technical text — get architecture-first 10-second explainers.</p>
        </div>
        <button @click="$emit('close')" class="rounded-lg px-2 py-1 text-slate-400 hover:bg-slate-100">✕</button>
      </div>

      <div class="space-y-3 overflow-y-auto px-5 py-4">
        <textarea
          v-model="content"
          rows="6"
          placeholder="Paste code, a config file, an error trace, or any technical content…"
          class="w-full rounded-xl border border-slate-300 bg-slate-50 p-3 font-mono text-xs outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
        ></textarea>
        <div class="flex gap-2">
          <input
            v-model="language"
            placeholder="Language (optional, e.g. python)"
            class="w-1/2 rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
          />
          <input
            v-model="contextNote"
            placeholder="Context (optional, e.g. auth module)"
            class="w-1/2 rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
          />
        </div>
        <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{{ error }}</p>
        <div v-if="result || busy" class="rounded-xl bg-slate-900 p-4">
          <pre class="whitespace-pre-wrap font-mono text-xs leading-relaxed text-emerald-100">{{ result }}<span v-if="busy" class="animate-pulse">▍</span></pre>
        </div>
      </div>

      <div class="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">
        <button @click="$emit('close')" class="rounded-xl px-4 py-2 text-sm text-slate-600 hover:bg-slate-100">Close</button>
        <button
          @click="generate"
          :disabled="busy || !content.trim()"
          class="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >{{ busy ? 'Explaining…' : '⚡ Generate Bytes' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { streamKnowledgeBytes } from '../services/api.js';

defineProps({ open: { type: Boolean, default: false } });
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
