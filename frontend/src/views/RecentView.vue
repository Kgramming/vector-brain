<template>
  <div class="vb-page">
    <div class="vb-page-head vb-rise">
      <div>
        <h1>Recent</h1>
        <p>Your latest documents, questions, and conversations.</p>
      </div>
      <button v-if="hasAnything" class="vb-btn vb-btn-ghost vb-btn-sm" @click="clearAll">Clear history</button>
    </div>

    <EmptyState
      v-if="!hasAnything"
      icon="clock" title="Nothing recent yet"
      description="Documents you open and questions you ask will show up here."
      compact
    />

    <template v-else>
      <section v-if="recentDocObjs.length" class="vb-section">
        <h2>Recently opened documents</h2>
        <div class="vb-doc-grid">
          <DocCard
            v-for="d in recentDocObjs.slice(0, 4)" :key="d.id" :doc="d" layout="grid"
            @open="$emit('open-doc', $event)" @delete="$emit('delete-doc', $event)" @toggle-fav="$emit('toggle-fav', $event)"
          />
        </div>
      </section>

      <section v-if="recentQuestions.length" class="vb-section">
        <h2>Recent questions</h2>
        <div class="vb-rows">
          <button v-for="rq in recentQuestions" :key="rq.at + rq.q" class="vb-row" @click="$emit('ask-again', rq.q)">
            <VbIcon name="chat" :size="16" />
            <span class="vb-row-text">{{ rq.q }}</span>
            <span v-if="rq.declined" class="vb-chip">no answer</span>
            <span class="vb-row-time">{{ timeAgo(rq.at) }}</span>
          </button>
        </div>
      </section>

      <section v-if="conversations.length" class="vb-section">
        <div class="vb-section-head">
          <h2>Saved conversations</h2>
          <button class="vb-btn vb-btn-ghost vb-btn-sm" @click="clearConvos">Clear all</button>
        </div>
        <div class="vb-rows">
          <div v-for="c in conversations" :key="c.id" class="vb-row vb-row-static">
            <VbIcon name="chat" :size="16" />
            <span class="vb-row-text">{{ c.title }}</span>
            <span class="vb-row-time">{{ timeAgo(c.at) }} · {{ c.messages.length }} messages</span>
            <button class="vb-icon-btn" @click="removeConversation(c.id)" aria-label="Delete conversation">
              <VbIcon name="trash" :size="15" />
            </button>
          </div>
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
import { timeAgo } from '../utils/format.js';
import { useRecents, useChatHistory } from '../composables/usePrefs.js';

const props = defineProps({ documents: { type: Array, default: () => [] } });
defineEmits(['navigate', 'open-doc', 'delete-doc', 'toggle-fav', 'ask-again']);

const { recentDocs, recentQuestions, clearQuestions } = useRecents();
const { conversations, removeConversation, clearAll: clearConvos } = useChatHistory();

const recentDocObjs = computed(() =>
  recentDocs.value
    .map(r => props.documents.find(d => d.id === r.id))
    .filter(Boolean)
);
const hasAnything = computed(() =>
  recentDocObjs.value.length || recentQuestions.value.length || conversations.value.length);

function clearAll() {
  clearQuestions();
  clearConvos();
}
</script>

<style scoped>
.vb-page { max-width: 1120px; margin: 0 auto; display: flex; flex-direction: column; gap: 22px; }
.vb-page-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.vb-page-head h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px; }
.vb-page-head p { font-size: 13.5px; color: var(--text-2); margin: 0; }
.vb-section h2 { font-size: 16px; font-weight: 700; margin: 0 0 12px; letter-spacing: -0.01em; }
.vb-section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.vb-section-head h2 { margin: 0; font-size: 16px; font-weight: 700; }
.vb-doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
.vb-rows { display: flex; flex-direction: column; gap: 8px; }
.vb-row {
  display: flex; align-items: center; gap: 12px; text-align: left; width: 100%;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 12px 16px; cursor: pointer; font-size: 13.5px; color: var(--text-2);
  transition: border-color var(--dur-fast);
}
.vb-row:not(.vb-row-static):hover { border-color: var(--accent-border); color: var(--text-1); }
.vb-row svg { color: var(--accent); flex-shrink: 0; }
.vb-row-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.vb-row-time { font-size: 12px; color: var(--text-3); flex-shrink: 0; }
.vb-icon-btn {
  width: 30px; height: 30px; border-radius: 8px; border: 0; background: none;
  display: inline-flex; align-items: center; justify-content: center;
  color: var(--text-3); cursor: pointer;
}
.vb-icon-btn:hover { background: var(--danger-soft); color: var(--danger); }
</style>
