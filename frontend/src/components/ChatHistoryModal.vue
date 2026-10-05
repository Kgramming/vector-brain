<template>
  <div class="vb-modal-backdrop" @click.self="$emit('close')" role="dialog" aria-modal="true" aria-label="Chat history">
    <div class="vb-modal vb-history-modal">
      <div class="vb-history-head">
        <div>
          <h2>Chat history</h2>
          <p>Previous Notebook conversations, newest first.</p>
        </div>
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="$emit('close')" aria-label="Close">
          <VbIcon name="x" :size="18" />
        </button>
      </div>

      <div v-if="!conversations.length" class="vb-history-empty">
        <VbIcon name="clock" :size="28" />
        <p>No saved conversations yet.<br />Ask a question, then start a new chat to save it here.</p>
      </div>

      <ul v-else class="vb-history-list">
        <li v-for="c in conversations" :key="c.id">
          <button class="vb-history-item" :class="{ current: c.id === currentId }" @click="$emit('open', c)">
            <span class="vb-history-main">
              <strong :title="c.title">{{ c.title || 'Conversation' }}</strong>
              <span class="vb-history-meta">
                {{ formatDate(c.at) }} · {{ countMessages(c) }} {{ countMessages(c) === 1 ? 'message' : 'messages' }}
              </span>
            </span>
            <span v-if="c.id === currentId" class="vb-history-badge">current</span>
          </button>
          <button
            class="vb-btn vb-btn-ghost vb-btn-icon vb-history-del"
            @click.stop="$emit('delete', c.id)"
            :aria-label="`Delete conversation ${c.title || ''}`"
            title="Delete conversation"
          >
            <VbIcon name="trash" :size="15" />
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import VbIcon from './VbIcon.vue';
import { formatDate } from '../utils/format.js';

defineProps({
  conversations: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
});
defineEmits(['close', 'open', 'delete']);

function countMessages(c) {
  return (c.messages || []).length;
}
</script>

<style scoped>
.vb-history-modal { max-width: 560px; }
.vb-history-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; margin-bottom: 6px;
}
.vb-history-head h2 { font-size: 17px; font-weight: 800; margin: 0 0 4px; letter-spacing: -0.01em; }
.vb-history-head p { font-size: 13px; color: var(--text-3); margin: 0; }
.vb-history-empty {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 36px 20px; color: var(--text-3); font-size: 13.5px; line-height: 1.6; text-align: center;
}
.vb-history-list {
  list-style: none; margin: 12px 0 0; padding: 0;
  display: flex; flex-direction: column; gap: 8px;
  max-height: 55vh; overflow-y: auto; min-height: 0;
}
.vb-history-list li { display: flex; gap: 6px; align-items: stretch; }
.vb-history-item {
  flex: 1; min-width: 0; display: flex; align-items: center; gap: 10px;
  background: var(--surface-2); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 12px 14px; cursor: pointer; text-align: left;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.vb-history-item:hover { border-color: var(--accent-border); box-shadow: var(--shadow-sm); }
.vb-history-item.current { border-color: var(--accent); }
.vb-history-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.vb-history-main strong {
  font-size: 13.5px; font-weight: 600; color: var(--text-1);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.vb-history-meta { font-size: 12px; color: var(--text-3); }
.vb-history-badge {
  font: 700 10.5px var(--font-sans); text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--accent); background: var(--accent-soft);
  border-radius: 999px; padding: 4px 10px; flex-shrink: 0;
}
.vb-history-del { flex-shrink: 0; align-self: center; }
.vb-history-del:hover { color: var(--danger); }
</style>
