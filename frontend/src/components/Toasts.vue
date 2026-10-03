<template>
  <div class="vb-toasts" role="status" aria-live="polite">
    <div
      v-for="t in toasts" :key="t.id"
      class="vb-toast"
      :class="{ leaving: t.leaving }"
    >
      <VbIcon
        :name="t.kind === 'success' ? 'check' : t.kind === 'error' ? 'alert' : 'info'"
        :size="17"
        :style="{ color: t.kind === 'success' ? 'var(--success)' : t.kind === 'error' ? 'var(--danger)' : 'var(--accent)', flexShrink: 0, marginTop: '1px' }"
      />
      <span style="flex: 1">{{ t.message }}</span>
      <button
        class="vb-toast-x"
        @click="dismiss(t.id)"
        aria-label="Dismiss notification"
      ><VbIcon name="x" :size="14" /></button>
    </div>
  </div>
</template>

<script setup>
import VbIcon from './VbIcon.vue';
import { useToasts } from '../composables/useToasts.js';

const { toasts, dismiss } = useToasts();
</script>

<style scoped>
.vb-toast-x {
  border: 0; background: none; cursor: pointer;
  color: var(--text-3); padding: 2px; border-radius: 6px;
  display: inline-flex; flex-shrink: 0;
}
.vb-toast-x:hover { color: var(--text-1); background: var(--hover-bg); }
</style>
