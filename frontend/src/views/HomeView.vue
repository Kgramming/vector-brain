<template>
  <div class="vb-home">
    <!-- hero -->
    <section class="vb-hero vb-rise">
      <div class="vb-hero-copy">
        <p class="vb-hero-kicker">Your Second Brain</p>
        <h1>Upload your documents.<br />Ask questions. Discover connections.</h1>
        <p class="vb-hero-sub">
          Vector-Brain reads your PDFs, understands them semantically, and answers
          with citations to the exact passages — across your whole library.
        </p>
        <div class="vb-hero-cta">
          <button class="vb-btn vb-btn-primary" @click="$emit('upload')">
            <VbIcon name="plus" :size="16" /> Add Documents
          </button>
          <button class="vb-btn vb-btn-secondary" @click="$emit('navigate', 'notebook')" :disabled="!readyCount">
            <VbIcon name="chat" :size="16" /> Open Notebook
          </button>
        </div>
        <p v-if="health?.groq_mode === 'mock'" class="vb-hero-note">
          <VbIcon name="info" :size="14" />
          Running in mock mode — set <code>GROQ_API_KEY</code> for live answers.
        </p>
      </div>
      <div class="vb-hero-art" aria-hidden="true">
        <div class="vb-hero-orb" />
        <div class="vb-hero-card vb-hero-card-1">
          <VbIcon name="file" :size="18" />
          <div><strong>Neural_Networks.pdf</strong><span>p. 42 · indexed</span></div>
        </div>
        <div class="vb-hero-card vb-hero-card-2">
          <VbIcon name="chat" :size="18" />
          <div><strong>“How does backprop work?”</strong><span>3 sources cited</span></div>
        </div>
      </div>
    </section>

    <!-- stats -->
    <section class="vb-stats" aria-label="Library statistics">
      <div class="vb-card vb-stat" v-for="s in stats" :key="s.label">
        <div class="vb-stat-icon"><VbIcon :name="s.icon" :size="20" /></div>
        <div>
          <p class="vb-stat-value">{{ s.value }}</p>
          <p class="vb-stat-label">{{ s.label }}</p>
        </div>
      </div>
    </section>

    <!-- empty onboarding -->
    <EmptyState
      v-if="!documents.length && !loading"
      icon="library"
      title="Your research workspace is empty"
      description="Upload your first PDF to get started. Vector-Brain will parse it with Docling, index it into PostgreSQL + pgvector, and make it searchable in seconds."
    >
      <template #actions>
        <button class="vb-btn vb-btn-primary" @click="$emit('upload')">
          <VbIcon name="upload" :size="16" /> Upload your first PDF
        </button>
        <button class="vb-btn vb-btn-ghost" @click="$emit('navigate', 'library')">How it works</button>
      </template>
    </EmptyState>

    <template v-else>
      <!-- recent documents -->
      <section class="vb-section">
        <div class="vb-section-head">
          <h2>Recent documents</h2>
          <button class="vb-btn vb-btn-ghost vb-btn-sm" @click="$emit('navigate', 'library')">
            View all <VbIcon name="chevRight" :size="14" />
          </button>
        </div>
        <div v-if="loading" class="vb-doc-grid">
          <div v-for="i in 3" :key="i" class="vb-skeleton" style="height: 190px" />
        </div>
        <div v-else class="vb-doc-grid">
          <DocCard
            v-for="d in recentDocs" :key="d.id" :doc="d" layout="grid"
            @open="$emit('open-doc', $event)" @delete="$emit('delete-doc', $event)" @toggle-fav="$emit('toggle-fav', $event)"
          />
        </div>
      </section>

      <!-- recent questions -->
      <section class="vb-section" v-if="recentQuestions.length">
        <div class="vb-section-head">
          <h2>Recent questions</h2>
          <button class="vb-btn vb-btn-ghost vb-btn-sm" @click="$emit('navigate', 'notebook')">Open Notebook <VbIcon name="chevRight" :size="14" /></button>
        </div>
        <div class="vb-questions">
          <button
            v-for="rq in recentQuestions.slice(0, 5)" :key="rq.at + rq.q"
            class="vb-question-row"
            @click="$emit('ask-again', rq.q)"
          >
            <VbIcon name="chat" :size="16" />
            <span class="vb-question-text">{{ rq.q }}</span>
            <span class="vb-question-time">{{ timeAgo(rq.at) }}</span>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import VbIcon from '../components/VbIcon.vue';
import EmptyState from '../components/EmptyState.vue';
import DocCard from '../components/DocCard.vue';
import { formatNumber, timeAgo } from '../utils/format.js';
import { useRecents } from '../composables/usePrefs.js';

const props = defineProps({
  documents: { type: Array, default: () => [] },
  health: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  totalPages: { type: Number, default: 0 },
  totalChunks: { type: Number, default: 0 },
});
defineEmits(['upload', 'navigate', 'open-doc', 'delete-doc', 'toggle-fav', 'ask-again']);

const { recentQuestions } = useRecents();

const readyCount = computed(() => props.documents.filter(d => d.status === 'ready').length);
const recentDocs = computed(() => props.documents.slice(0, 3));

const stats = computed(() => [
  { icon: 'library', label: 'Documents', value: formatNumber(props.documents.length) },
  { icon: 'book', label: 'Pages indexed', value: formatNumber(props.totalPages) },
  { icon: 'layers', label: 'Vector chunks', value: formatNumber(props.totalChunks) },
  { icon: 'chat', label: 'Questions asked', value: formatNumber(recentQuestions.value.length) },
]);
</script>

<style scoped>
.vb-home { display: flex; flex-direction: column; gap: var(--pad-section); max-width: 1120px; margin: 0 auto; }

.vb-hero {
  display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 32px; align-items: center;
  padding: 40px 36px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm); overflow: hidden; position: relative;
}
.vb-hero-kicker {
  font: 700 12px/1 var(--font-sans); letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent); margin: 0 0 12px;
}
.vb-hero h1 {
  font-size: clamp(28px, 4vw, 40px); font-weight: 800; letter-spacing: -0.02em; line-height: 1.15;
  margin: 0 0 14px; color: var(--text-1);
}
.vb-hero-sub { font-size: 15px; color: var(--text-2); line-height: 1.65; margin: 0 0 24px; max-width: 480px; }
.vb-hero-cta { display: flex; gap: 12px; flex-wrap: wrap; }
.vb-hero-note {
  display: flex; align-items: center; gap: 8px;
  margin: 18px 0 0; font-size: 12.5px; color: var(--warning);
}
.vb-hero-note code { font-family: var(--font-mono); font-size: 11.5px; background: var(--warning-soft); padding: 1px 6px; border-radius: 6px; }

.vb-hero-art { position: relative; min-height: 220px; }
.vb-hero-orb {
  position: absolute; inset: 10% 5%; border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, var(--accent-soft), transparent 70%);
  filter: blur(10px);
}
.vb-hero-card {
  position: absolute; display: flex; gap: 12px; align-items: center;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 14px 16px; box-shadow: var(--shadow-md);
  color: var(--accent); max-width: 260px;
  animation: vb-float 6s ease-in-out infinite;
}
.vb-hero-card div { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.vb-hero-card strong { font-size: 13px; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-hero-card span { font-size: 11.5px; color: var(--text-3); }
.vb-hero-card-1 { top: 8%; left: 4%; }
.vb-hero-card-2 { bottom: 10%; right: 2%; animation-delay: -3s; }
@keyframes vb-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }

.vb-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.vb-stat { padding: 18px; display: flex; gap: 14px; align-items: center; }
.vb-stat-icon {
  width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent-soft); color: var(--accent);
}
.vb-stat-value { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin: 0; line-height: 1.1; }
.vb-stat-label { font-size: 12.5px; color: var(--text-3); margin: 2px 0 0; }

.vb-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.vb-section-head h2 { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; margin: 0; }
.vb-doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }

.vb-questions { display: flex; flex-direction: column; gap: 8px; }
.vb-question-row {
  display: flex; align-items: center; gap: 12px; text-align: left;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 13px 16px; cursor: pointer; color: var(--text-2);
  transition: border-color var(--dur-fast), transform var(--dur-fast);
  font-size: 13.5px;
}
.vb-question-row:hover { border-color: var(--accent-border); transform: translateX(2px); color: var(--text-1); }
.vb-question-row svg { color: var(--accent); flex-shrink: 0; }
.vb-question-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.vb-question-time { font-size: 12px; color: var(--text-3); flex-shrink: 0; }

@media (max-width: 900px) {
  .vb-hero { grid-template-columns: 1fr; padding: 28px 24px; }
  .vb-hero-art { display: none; }
  .vb-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
