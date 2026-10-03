<template>
  <div class="flex h-full flex-col rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
    <div class="border-b border-slate-100 px-5 py-3">
      <h2 class="font-semibold text-slate-800">Notebook chat</h2>
      <p class="text-xs text-slate-500">Ask across all your PDFs — answers cite their sources.</p>
    </div>

    <div ref="scrollBox" class="flex-1 space-y-4 overflow-y-auto px-5 py-4">
      <div v-if="!messages.length" class="py-8 text-center text-sm text-slate-400">
        <p class="text-3xl mb-2">🧠</p>
        <p>Your second brain is ready.<br />Ask something your documents can answer.</p>
      </div>

      <div v-for="(m, i) in messages" :key="i">
        <!-- user -->
        <div v-if="m.role === 'user'" class="flex justify-end">
          <div class="max-w-[85%] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5 text-sm text-white">{{ m.content }}</div>
        </div>
        <!-- assistant -->
        <div v-else class="flex justify-start">
          <div class="max-w-[92%] rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3">
            <p class="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">{{ m.content }}<span v-if="m.streaming" class="animate-pulse">▍</span></p>
            <div v-if="!m.streaming && m.sources.length" class="mt-3 border-t border-slate-200 pt-2">
              <p class="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</p>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="s in m.sources" :key="s.rank"
                  @click="selected = selected?.rank === s.rank && selectedMsg === i ? null : { ...s, msg: i }; selectedMsg = i"
                  class="rounded-full px-2.5 py-1 text-xs font-medium ring-1 transition-colors"
                  :class="selected?.rank === s.rank && selectedMsg === i ? 'bg-indigo-600 text-white ring-indigo-600' : 'bg-white text-indigo-700 ring-indigo-200 hover:bg-indigo-50'"
                  :title="`${s.title} — similarity ${s.similarity}`"
                >[{{ s.rank }}] {{ shortName(s.title) }}</button>
              </div>
              <div v-if="selected && selectedMsg === i" class="mt-2 rounded-xl bg-white p-3 text-xs ring-1 ring-slate-200">
                <p class="mb-1 font-semibold text-slate-700">
                  [{{ selected.rank }}] {{ selected.title }}
                  <span v-if="selected.page_start" class="font-normal text-slate-500">· p. {{ selected.page_start }}<span v-if="selected.page_end && selected.page_end !== selected.page_start">–{{ selected.page_end }}</span></span>
                  <span class="ml-1 font-normal text-slate-400">· sim {{ selected.similarity }}</span>
                </p>
                <p class="whitespace-pre-wrap leading-relaxed text-slate-600">{{ selected.excerpt }}{{ selected.excerpt.length >= 500 ? '…' : '' }}</p>
              </div>
            </div>
            <p v-if="!m.streaming && m.declined" class="mt-2 text-xs italic text-slate-500">No supporting passages found — no citations attached.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="border-t border-slate-100 px-5 py-3">
      <p v-if="error" class="mb-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{{ error }}</p>
      <div class="flex gap-2">
        <input
          v-model="draft"
          @keyup.enter="send"
          :disabled="busy"
          placeholder="Ask a question across your PDFs…"
          class="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 disabled:bg-slate-50"
        />
        <button
          @click="send"
          :disabled="busy || !draft.trim()"
          class="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >{{ busy ? '…' : 'Ask' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { streamChat } from '../services/api.js';

const messages = ref([]);
const draft = ref('');
const busy = ref(false);
const error = ref('');
const selected = ref(null);
const selectedMsg = ref(null);
const scrollBox = ref(null);

function shortName(title) {
  const t = title || 'doc';
  return t.length > 22 ? t.slice(0, 20) + '…' : t;
}

function scrollDown() {
  nextTick(() => { if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight; });
}

async function send() {
  const q = draft.value.trim();
  if (!q || busy.value) return;
  error.value = '';
  messages.value.push({ role: 'user', content: q });
  draft.value = '';
  busy.value = true;
  const ans = { role: 'assistant', content: '', sources: [], declined: false, streaming: true };
  messages.value.push(ans);
  scrollDown();
  try {
    await streamChat(q, {
      onSources: (s) => { ans.sources = s; },
      onToken: (t) => { ans.content += t; scrollDown(); },
      onDone: ({ declined }) => { ans.declined = !!declined; ans.streaming = false; busy.value = false; scrollDown(); },
      onError: (e) => { throw e; },
    });
  } catch (e) {
    error.value = e.message || 'Chat failed';
    ans.content += '\n⚠️ ' + (e.message || 'Chat failed');
    ans.streaming = false;
    busy.value = false;
  }
}
</script>
