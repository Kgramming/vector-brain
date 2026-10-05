<template>
  <div class="vb-notebook">
    <!-- left: scope selector -->
    <aside class="vb-scope" :class="{ open: scopeOpen }" aria-label="Document scope">
      <div class="vb-scope-head">
        <h2>Search across</h2>
        <button class="vb-btn vb-btn-ghost vb-btn-icon vb-scope-close" @click="scopeOpen = false" aria-label="Close panel">
          <VbIcon name="x" :size="16" />
        </button>
      </div>
      <label class="vb-scope-all">
        <input type="checkbox" :checked="allSelected" @change="toggleAll" />
        <span class="vb-scope-all-text">
          <strong>All documents</strong>
          <small>{{ readyDocs.length }} ready</small>
        </span>
      </label>
      <div class="vb-scope-list">
        <label v-for="d in readyDocs" :key="d.id" class="vb-scope-item" :title="d.filename">
          <input type="checkbox" :checked="selectedIds.has(d.id)" @change="toggleDoc(d.id)" />
          <VbIcon name="file" :size="15" class="vb-scope-file" />
          <span class="vb-scope-name">{{ d.filename }}</span>
        </label>
        <p v-if="!readyDocs.length" class="vb-scope-empty">
          No indexed documents yet.
          <button class="vb-link" @click="$emit('upload')">Upload a PDF</button> to start asking.
        </p>
      </div>
      <div class="vb-scope-foot">
        <button class="vb-btn vb-btn-ghost vb-btn-sm" @click="newChat">
          <VbIcon name="plus" :size="14" /> New chat
        </button>
        <button class="vb-btn vb-btn-ghost vb-btn-sm" @click="historyOpen = true" title="Browse previous conversations">
          <VbIcon name="clock" :size="14" /> History
        </button>
      </div>
    </aside>

    <!-- center: conversation -->
    <section class="vb-chat" aria-label="Conversation">
      <div class="vb-chat-head">
        <button class="vb-btn vb-btn-ghost vb-btn-icon vb-scope-toggle" @click="scopeOpen = !scopeOpen" aria-label="Toggle document scope">
          <VbIcon name="panel" :size="18" />
        </button>
        <div class="vb-chat-title">
          <h1>{{ convoTitle }}</h1>
          <p>{{ scopeSummary }}</p>
        </div>
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="sourcesOpen = !sourcesOpen" :title="sourcesOpen ? 'Hide sources' : 'Show sources'" aria-label="Toggle sources panel">
          <VbIcon name="book" :size="18" />
        </button>
      </div>

      <div ref="scrollBox" class="vb-messages">
        <!-- empty state -->
        <div v-if="!messages.length" class="vb-chat-empty">
          <div class="vb-chat-empty-icon"><VbIcon name="brain" :size="32" /></div>
          <h2>Ask your second brain</h2>
          <p>Answers are grounded in your documents and cite their sources.</p>
          <p class="vb-prompts-label">Try asking</p>
          <div class="vb-prompts">
            <button v-for="p in examplePrompts" :key="p" class="vb-prompt" @click="askExample(p)">
              {{ p }}
            </button>
          </div>
        </div>

        <!-- messages -->
        <div v-for="(m, i) in messages" :key="i" class="vb-msg vb-rise" :class="m.role">
          <div v-if="m.role === 'user'" class="vb-user-bubble">{{ m.content }}</div>
          <div v-else class="vb-ai-bubble">
            <div class="vb-prose" v-html="rendered(m)" :ref="el => bindMsg(el, i)" />
            <span v-if="m.streaming" class="vb-caret" aria-hidden="true" />
            <div v-if="!m.streaming && m.sources.length" class="vb-src-chips">
              <button
                v-for="s in m.sources" :key="s.rank"
                class="vb-src-chip" :class="{ active: activeMsg === i && activeRank === s.rank }"
                @click="showSource(i, s.rank)"
                :title="`${s.title} · ${pageLabel(s.page_start, s.page_end)} · similarity ${s.similarity}`"
              >[{{ s.rank }}] {{ shortName(s.title, 24) }}</button>
            </div>
            <p v-if="!m.streaming && m.declined" class="vb-declined">
              No supporting passages found — no citations attached. Try uploading the relevant PDF.
            </p>
          </div>
        </div>

        <div v-if="busy && !streamingMsg" class="vb-thinking" aria-label="Thinking">
          <span class="vb-think-dot" /><span class="vb-think-dot" /><span class="vb-think-dot" />
        </div>
      </div>

      <div class="vb-composer">
        <p v-if="error" class="vb-composer-error" role="alert">{{ error }}</p>
        <div class="vb-composer-row">
          <textarea
            ref="inputEl" v-model="draft" rows="1"
            placeholder="Ask a question across your documents…"
            aria-label="Ask a question"
            :disabled="busy || !readyDocs.length"
            @keydown="onKeydown"
            @input="autosize"
          />
          <button
            class="vb-btn vb-btn-primary vb-send"
            @click="send" :disabled="busy || !draft.trim() || !readyDocs.length"
            aria-label="Send question"
          ><VbIcon name="send" :size="16" /></button>
        </div>
        <p class="vb-composer-hint">
          <span class="vb-kbd">⌘</span><span class="vb-kbd">↵</span> to send
          · answers cite [n] sources from your library
        </p>
      </div>
    </section>

    <!-- right: sources -->
    <aside class="vb-sources" :class="{ open: sourcesOpen }" aria-label="Sources">
      <div class="vb-sources-head">
        <h2>Sources</h2>
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="sourcesOpen = false" aria-label="Close sources">
          <VbIcon name="x" :size="16" />
        </button>
      </div>
      <div v-if="!activeSources.length" class="vb-sources-empty">
        <VbIcon name="book" :size="24" />
        <p>Ask a question and the passages behind each answer will appear here.</p>
      </div>
      <div v-else class="vb-source-list">
        <article
          v-for="s in activeSources" :key="s.rank"
          class="vb-source-card" :class="{ highlight: s.rank === activeRank }"
          :ref="el => sourceRefs[s.rank] = el"
        >
          <div class="vb-source-top">
            <span class="vb-source-rank">[{{ s.rank }}]</span>
            <div class="vb-source-meta">
              <strong :title="s.title">{{ shortName(s.title, 30) }}</strong>
              <span>{{ pageLabel(s.page_start, s.page_end) }} · relevance {{ relevanceLabel(s.similarity) }}</span>
            </div>
          </div>
          <p class="vb-source-excerpt">{{ s.excerpt }}{{ s.excerpt.length >= 500 ? '…' : '' }}</p>
          <div class="vb-source-bar"><div :style="{ width: Math.round(s.similarity * 100) + '%' }" /></div>
        </article>
      </div>
    </aside>

    <ChatHistoryModal
      v-if="historyOpen"
      :conversations="conversations"
      :current-id="currentConvoId"
      @close="historyOpen = false"
      @open="openConversation"
      @delete="deleteConversation"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue';
import VbIcon from '../components/VbIcon.vue';
import { streamChat } from '../services/api.js';
import { renderMarkdown, bindCitations } from '../utils/markdown.js';
import { shortName, pageLabel, relevanceLabel, filterSourcesToCited } from '../utils/format.js';
import { useRecents, useChatHistory, usePrefs } from '../composables/usePrefs.js';
import { useToasts } from '../composables/useToasts.js';
import ChatHistoryModal from '../components/ChatHistoryModal.vue';

const props = defineProps({
  documents: { type: Array, default: () => [] },
  // set by App when navigating from Library/Home with a preselected scope or question
  presetDocIds: { type: Array, default: () => [] },
  presetQuestion: { type: String, default: '' },
});
const emit = defineEmits(['upload']);

const { pushQuestion } = useRecents();
const { conversations, saveConversation, removeConversation } = useChatHistory();
const { notebookPrefs } = usePrefs();
const { error: toastError } = useToasts();

const readyDocs = computed(() => props.documents.filter(d => d.status === 'ready'));
const selectedIds = ref(new Set());
const scopeOpen = ref(true);
const sourcesOpen = ref(true);
const historyOpen = ref(false);
const currentConvoId = ref(null);

const messages = ref([]);
const draft = ref('');
const busy = ref(false);
const error = ref('');
const scrollBox = ref(null);
const inputEl = ref(null);
const streamingMsg = ref(false);

const activeMsg = ref(null);
const activeRank = ref(null);
const sourceRefs = {};
const activeSources = computed(() => {
  if (activeMsg.value == null) {
    // default: sources of the latest assistant message
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'assistant' && messages.value[i].sources.length) return messages.value[i].sources;
    }
    return [];
  }
  return messages.value[activeMsg.value]?.sources || [];
});

const allSelected = computed(() =>
  readyDocs.value.length > 0 && selectedIds.value.size === readyDocs.value.length);
const scopeSummary = computed(() => {
  if (!readyDocs.value.length) return 'No documents indexed yet';
  if (allSelected.value) return `All documents · ${readyDocs.value.length} in scope`;
  if (!selectedIds.value.size) return 'No documents selected';
  return `${selectedIds.value.size} of ${readyDocs.value.length} documents in scope`;
});
const convoTitle = computed(() => {
  const first = messages.value.find(m => m.role === 'user');
  if (!first) return 'New conversation';
  return first.content.length > 48 ? first.content.slice(0, 47) + '…' : first.content;
});

const examplePrompts = [
  'Summarize the key concepts across these documents.',
  'What are the main differences between the approaches described?',
  'Find evidence supporting the central claim.',
  'Explain the core topic in simple terms.',
];

function toggleDoc(id) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id); else next.add(id);
  selectedIds.value = next;
}
function toggleAll() {
  selectedIds.value = allSelected.value ? new Set() : new Set(readyDocs.value.map(d => d.id));
}

function rendered(m) {
  return renderMarkdown(m.content || '');
}
const unbinders = new Map();
function bindMsg(el, i) {
  if (!el) return;
  if (unbinders.has(i)) unbinders.get(i)();
  unbinders.set(i, bindCitations(el, (rank) => showSource(i, rank)));
}
onUnmounted(() => unbinders.forEach(u => u()));

function showSource(msgIdx, rank) {
  activeMsg.value = msgIdx;
  activeRank.value = rank;
  sourcesOpen.value = true;
  nextTick(() => {
    sourceRefs[rank]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
}

function scrollDown() {
  nextTick(() => {
    if (scrollBox.value) scrollBox.value.scrollTo({ top: scrollBox.value.scrollHeight, behavior: 'smooth' });
  });
}
function autosize() {
  const el = inputEl.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}
function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); send(); }
  else if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
}

function askExample(p) {
  draft.value = p;
  autosize();
  send();
}

function snapshotMessages() {
  return messages.value.map(m => ({
    role: m.role,
    content: m.content,
    sources: m.sources || [],
    declined: !!m.declined,
  }));
}

function scopeIdsOrNull() {
  // null = all documents in scope; otherwise the explicit selection
  return allSelected.value ? null : [...selectedIds.value];
}

/** Persist the current conversation (upsert by id). Called after each answer. */
function persistCurrent() {
  if (!messages.value.length) return;
  if (!currentConvoId.value) currentConvoId.value = 'c' + Date.now();
  const firstUser = messages.value.find(m => m.role === 'user');
  saveConversation({
    id: currentConvoId.value,
    title: firstUser ? firstUser.content.slice(0, 60) : 'Conversation',
    at: Date.now(),
    scopeIds: scopeIdsOrNull(),
    messages: snapshotMessages(),
  });
  try { localStorage.setItem('vb:currentConvoId', currentConvoId.value); } catch { /* ignore */ }
}

function newChat() {
  persistCurrent();
  messages.value = [];
  currentConvoId.value = null;
  try { localStorage.removeItem('vb:currentConvoId'); } catch { /* ignore */ }
  activeMsg.value = null;
  activeRank.value = null;
  error.value = '';
  nextTick(() => inputEl.value?.focus());
}

function openConversation(conv) {
  persistCurrent();
  messages.value = (conv.messages || []).map(m => ({
    role: m.role,
    content: m.content || '',
    sources: m.sources || [],
    declined: !!m.declined,
    streaming: false,
  }));
  currentConvoId.value = conv.id;
  // restore the document scope used by this conversation (if docs still exist)
  if (Array.isArray(conv.scopeIds)) {
    const valid = new Set(readyDocs.value.map(d => d.id));
    const ids = conv.scopeIds.filter(id => valid.has(id));
    if (ids.length) selectedIds.value = new Set(ids);
  } else if (conv.scopeIds === null) {
    selectedIds.value = new Set(readyDocs.value.map(d => d.id));
  }
  activeMsg.value = null;
  activeRank.value = null;
  error.value = '';
  historyOpen.value = false;
  nextTick(() => { scrollBox.value?.scrollTo({ top: 0 }); inputEl.value?.focus(); });
}

function deleteConversation(id) {
  removeConversation(id);
  if (currentConvoId.value === id) {
    currentConvoId.value = null;
    messages.value = [];
    activeMsg.value = null;
    activeRank.value = null;
  }
}

async function send() {
  const q = draft.value.trim();
  if (!q || busy.value || !readyDocs.value.length) return;
  if (!selectedIds.value.size) {
    toastError('Select at least one document to search across.');
    return;
  }
  error.value = '';
  messages.value.push({ role: 'user', content: q });
  pushQuestion(q);
  draft.value = '';
  nextTick(autosize);
  busy.value = true;
  streamingMsg.value = true;
  messages.value.push({ role: 'assistant', content: '', sources: [], declined: false, streaming: true });
  // Mutate through the reactive proxy (not a raw local) so computeds invalidate.
  const ans = messages.value[messages.value.length - 1];
  scrollDown();

  const docIds = allSelected.value ? null : [...selectedIds.value];
  try {
    await streamChat(q, {
      onSources: (s) => { ans.sources = s; },
      onToken: (t) => { ans.content += t; scrollDown(); },
      onDone: ({ declined }) => {
        ans.declined = !!declined;
        ans.streaming = false;
        // Strict grounding: the Sources panel must correspond exactly to the
        // citations the model emitted — drop retrieved-but-uncited passages.
        ans.sources = ans.declined ? [] : filterSourcesToCited(ans.sources, ans.content);
        busy.value = false;
        streamingMsg.value = false;
        pushQuestion(q, ans.declined);
        persistCurrent();
        scrollDown();
      },
      onError: (e) => { throw e; },
    }, { topK: notebookPrefs.value.topK, documentIds: docIds });
  } catch (e) {
    error.value = e.message || 'Chat failed.';
    ans.content += '\n\n> ⚠️ ' + (e.message || 'Chat failed.');
    ans.streaming = false;
    busy.value = false;
    streamingMsg.value = false;
  }
}

// presets from navigation (Library "Open in Notebook", Home "ask again")
watch(() => props.presetDocIds, (ids) => {
  if (ids?.length) selectedIds.value = new Set(ids.filter(id => readyDocs.value.some(d => d.id === id)));
}, { immediate: true });
watch(() => readyDocs.value, (docs) => {
  // default scope: all ready docs (unless a preset narrowed it)
  if (!selectedIds.value.size && docs.length) selectedIds.value = new Set(docs.map(d => d.id));
  // drop ids of deleted docs
  const valid = new Set(docs.map(d => d.id));
  selectedIds.value = new Set([...selectedIds.value].filter(id => valid.has(id)));
}, { immediate: true });
watch(() => props.presetQuestion, (q) => {
  if (q) { draft.value = q; nextTick(() => { autosize(); send(); }); }
});

onMounted(() => {
  if (window.innerWidth < 1100) { scopeOpen.value = false; sourcesOpen.value = false; }
  // restore the in-progress conversation across page refreshes
  try {
    const cid = localStorage.getItem('vb:currentConvoId');
    if (cid) {
      const conv = conversations.value.find(c => c.id === cid);
      if (conv?.messages?.length) {
        messages.value = conv.messages.map(m => ({
          role: m.role, content: m.content || '', sources: m.sources || [],
          declined: !!m.declined, streaming: false,
        }));
        currentConvoId.value = conv.id;
      }
    }
  } catch { /* ignore */ }
  nextTick(() => inputEl.value?.focus());
});
</script>

<style scoped>
.vb-notebook {
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  gap: 0; height: 100%;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  min-height: 560px;
}

/* ---- left: scope ---- */
.vb-scope {
  border-right: 1px solid var(--border);
  background: var(--sidebar-bg);
  display: flex; flex-direction: column;
  padding: 18px 14px; overflow-y: auto;
  min-height: 0;
}
.vb-scope-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.vb-scope-head h2 { font-size: 14px; font-weight: 700; margin: 0; }
.vb-scope-close { display: none; }
.vb-scope-all {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: var(--radius-md); cursor: pointer;
  border: 1px solid var(--border); background: var(--surface); margin-bottom: 8px;
}
.vb-scope-all:hover { border-color: var(--accent-border); }
.vb-scope-all-text { display: flex; flex-direction: column; line-height: 1.35; }
.vb-scope-all-text strong { font-size: 13px; }
.vb-scope-all-text small { font-size: 11.5px; color: var(--text-3); }
.vb-scope input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--accent); flex-shrink: 0; cursor: pointer; }
.vb-scope-list { display: flex; flex-direction: column; gap: 2px; overflow-y: auto; min-height: 0; }
.vb-scope-item {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px; border-radius: var(--radius-md); cursor: pointer;
  font-size: 13px; color: var(--text-2);
}
.vb-scope-item:hover { background: var(--hover-bg); color: var(--text-1); }
.vb-scope-file { color: var(--accent); flex-shrink: 0; }
.vb-scope-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-scope-empty { font-size: 12.5px; color: var(--text-3); line-height: 1.6; padding: 8px; }
.vb-link { background: none; border: 0; color: var(--accent); font-weight: 600; cursor: pointer; padding: 0; font-size: inherit; }
.vb-scope-foot { margin-top: auto; padding-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }
.vb-scope-toggle { display: none; }

/* ---- center: chat ---- */
.vb-chat { display: flex; flex-direction: column; min-width: 0; min-height: 0; background: var(--bg); }
.vb-chat-head {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px; border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.vb-chat-title { flex: 1; min-width: 0; }
.vb-chat-title h1 { font-size: 15px; font-weight: 700; margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-chat-title p { font-size: 12px; color: var(--text-3); margin: 2px 0 0; }

.vb-messages { flex: 1; min-height: 0; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }
.vb-chat-empty { text-align: center; padding: 40px 20px; max-width: 560px; margin: 0 auto; }
.vb-chat-empty-icon {
  width: 64px; height: 64px; margin: 0 auto 18px; border-radius: 20px;
  background: var(--accent-soft); color: var(--accent);
  display: flex; align-items: center; justify-content: center;
}
.vb-chat-empty h2 { font-size: 22px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 8px; }
.vb-chat-empty > p { color: var(--text-2); font-size: 14px; margin: 0 0 28px; }
.vb-prompts-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-3); margin: 0 0 12px; text-align: left; }
.vb-prompts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: left; }
.vb-prompt {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 14px; font-size: 13px; color: var(--text-2); cursor: pointer; text-align: left;
  transition: border-color var(--dur-fast), transform var(--dur-fast), box-shadow var(--dur-fast);
  line-height: 1.5;
}
.vb-prompt:hover { border-color: var(--accent-border); transform: translateY(-1px); box-shadow: var(--shadow-sm); color: var(--text-1); }

.vb-msg.user { display: flex; justify-content: flex-end; }
.vb-user-bubble {
  max-width: 80%; background: var(--accent); color: var(--accent-contrast);
  padding: 11px 16px; border-radius: 18px 18px 6px 18px;
  font-size: 14px; line-height: 1.55; box-shadow: var(--shadow-sm);
  white-space: pre-wrap; word-wrap: break-word;
}
.vb-msg.assistant { display: flex; justify-content: flex-start; }
.vb-ai-bubble {
  max-width: 92%; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px 18px 18px 18px;
  padding: 16px 18px; box-shadow: var(--shadow-sm); min-width: 0;
}
.vb-caret {
  display: inline-block; width: 8px; height: 16px; margin-left: 4px;
  background: var(--accent); border-radius: 2px; vertical-align: -2px;
  animation: vb-pulse-dot 1s ease-in-out infinite;
}
.vb-src-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.vb-src-chip {
  font: 600 12px var(--font-sans); padding: 6px 10px; border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--border); color: var(--text-2); cursor: pointer;
  transition: all var(--dur-fast);
}
.vb-src-chip:hover { border-color: var(--accent-border); color: var(--accent); }
.vb-src-chip.active { background: var(--accent); border-color: var(--accent); color: var(--accent-contrast); }
.vb-declined { font-size: 12.5px; font-style: italic; color: var(--text-3); margin: 10px 0 0; }

.vb-thinking { display: flex; gap: 6px; padding: 4px 0; }
.vb-think-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-3); animation: vb-pulse-dot 1.2s ease-in-out infinite; }
.vb-think-dot:nth-child(2) { animation-delay: 0.15s; }
.vb-think-dot:nth-child(3) { animation-delay: 0.3s; }

.vb-composer { padding: 14px 18px 10px; border-top: 1px solid var(--border); background: var(--surface); }
.vb-composer-error {
  margin: 0 0 10px; padding: 10px 12px; border-radius: var(--radius-md);
  background: var(--danger-soft); color: var(--danger); font-size: 13px;
}
.vb-composer-row { display: flex; gap: 10px; align-items: flex-end; }
.vb-composer-row textarea {
  flex: 1; resize: none; max-height: 160px;
  background: var(--input-bg); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 11px 14px; font: 400 14px/1.5 var(--font-sans); color: var(--text-1);
}
.vb-composer-row textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.vb-send { padding: 11px 16px; flex-shrink: 0; }
.vb-composer-hint { margin: 8px 0 0; font-size: 11.5px; color: var(--text-3); display: flex; align-items: center; gap: 5px; }

/* ---- right: sources ---- */
.vb-sources {
  border-left: 1px solid var(--border); background: var(--sidebar-bg);
  display: flex; flex-direction: column; overflow: hidden;
  min-height: 0;
}
.vb-sources-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 16px 10px; }
.vb-sources-head h2 { font-size: 14px; font-weight: 700; margin: 0; }
.vb-sources-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: 12px; padding: 24px; color: var(--text-3); font-size: 13px; line-height: 1.6;
}
.vb-source-list { flex: 1; min-height: 0; overflow-y: auto; padding: 6px 14px 18px; display: flex; flex-direction: column; gap: 10px; }
.vb-source-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 12px 14px; transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.vb-source-card.highlight { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.vb-source-top { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; }
.vb-source-rank {
  font: 800 13px var(--font-mono); color: var(--accent);
  background: var(--accent-soft); border-radius: 8px; padding: 4px 8px; flex-shrink: 0;
}
.vb-source-meta { display: flex; flex-direction: column; min-width: 0; line-height: 1.4; }
.vb-source-meta strong { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-source-meta span { font-size: 11.5px; color: var(--text-3); }
.vb-source-excerpt { font-size: 12.5px; color: var(--text-2); line-height: 1.6; margin: 0 0 10px; }
.vb-source-bar { height: 4px; border-radius: 999px; background: var(--surface-3); overflow: hidden; }
.vb-source-bar div { height: 100%; background: var(--accent); border-radius: 999px; }

/* ---- responsive ---- */
@media (max-width: 1280px) {
  .vb-notebook { grid-template-columns: 230px 1fr 280px; }
}
@media (max-width: 1100px) {
  .vb-notebook { grid-template-columns: 1fr; position: relative; }
  .vb-scope, .vb-sources {
    position: absolute; top: 0; bottom: 0; z-index: 20; width: 300px; max-width: 85vw;
    transition: transform var(--dur-med) var(--ease-out);
    box-shadow: var(--shadow-lg);
  }
  .vb-scope { left: 0; transform: translateX(-105%); }
  .vb-scope.open { transform: none; }
  .vb-sources { right: 0; border-left: 1px solid var(--border); transform: translateX(105%); }
  .vb-sources.open { transform: none; }
  .vb-scope-toggle { display: inline-flex !important; }
  .vb-scope-close { display: inline-flex !important; }
}
@media (max-width: 640px) {
  .vb-prompts { grid-template-columns: 1fr; }
  .vb-messages { padding: 16px; }
  .vb-ai-bubble { max-width: 100%; }
}
</style>
