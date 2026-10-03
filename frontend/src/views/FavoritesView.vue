<template>
  <div class="vb-page">
    <div class="vb-page-head vb-rise">
      <div>
        <h1>Favorites</h1>
        <p>Starred documents — quick access to what matters most.</p>
      </div>
    </div>

    <EmptyState
      v-if="!favDocs.length"
      icon="star" title="No favorites yet"
      description="Star documents in the Library to pin them here for quick access."
      compact
    >
      <template #actions>
        <button class="vb-btn vb-btn-secondary vb-btn-sm" @click="$emit('navigate', 'library')">Browse Library</button>
      </template>
    </EmptyState>

    <div v-else class="vb-doc-grid">
      <DocCard
        v-for="d in favDocs" :key="d.id" :doc="d" layout="grid"
        @open="$emit('open-doc', $event)" @delete="$emit('delete-doc', $event)" @toggle-fav="$emit('toggle-fav', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import EmptyState from '../components/EmptyState.vue';
import DocCard from '../components/DocCard.vue';
import { useFavorites } from '../composables/usePrefs.js';

const props = defineProps({ documents: { type: Array, default: () => [] } });
defineEmits(['navigate', 'open-doc', 'delete-doc', 'toggle-fav']);

const { favorites } = useFavorites();
const favDocs = computed(() => props.documents.filter(d => favorites.value.includes(d.id)));
</script>

<style scoped>
.vb-page { max-width: 1120px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
.vb-page-head h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px; }
.vb-page-head p { font-size: 13.5px; color: var(--text-2); margin: 0; }
.vb-doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
</style>
