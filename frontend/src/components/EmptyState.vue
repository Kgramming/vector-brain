<template>
  <div class="vb-empty" :class="{ compact }">
    <div class="vb-empty-icon"><VbIcon :name="icon" :size="30" /></div>
    <h3 class="vb-empty-title">{{ title }}</h3>
    <p class="vb-empty-desc">{{ description }}</p>
    <div v-if="$slots.actions" class="vb-empty-actions"><slot name="actions" /></div>
  </div>
</template>

<script setup>
import VbIcon from './VbIcon.vue';

defineProps({
  icon: { type: String, default: 'info' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  compact: { type: Boolean, default: false },
});
</script>

<style scoped>
.vb-empty {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: 56px 24px; gap: 0;
}
.vb-empty.compact { padding: 32px 20px; }
.vb-empty-icon {
  width: 64px; height: 64px; border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent-soft); color: var(--accent);
  margin-bottom: 18px;
}
.vb-empty.compact .vb-empty-icon { width: 48px; height: 48px; border-radius: 14px; margin-bottom: 12px; }
.vb-empty-title { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; color: var(--text-1); margin: 0 0 8px; }
.vb-empty-desc { font-size: 13.5px; color: var(--text-2); max-width: 420px; line-height: 1.6; margin: 0; }
.vb-empty-actions { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; justify-content: center; }
</style>
