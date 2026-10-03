<template>
  <aside
    class="vb-sidebar"
    :class="{ collapsed }"
    role="navigation"
    aria-label="Primary"
  >
    <!-- logo -->
    <button class="vb-logo" @click="$emit('navigate', 'home')" title="Vector-Brain home">
      <span class="vb-logo-mark"><VbIcon name="brain" :size="22" /></span>
      <span v-if="!collapsed" class="vb-logo-text">
        <strong>Vector-Brain</strong>
        <small>Second Brain</small>
      </span>
    </button>

    <!-- primary nav -->
    <nav class="vb-nav">
      <button
        v-for="item in mainNav" :key="item.id"
        class="vb-nav-item"
        :class="{ active: view === item.id }"
        :title="collapsed ? item.label : ''"
        :aria-current="view === item.id ? 'page' : undefined"
        @click="$emit('navigate', item.id)"
      >
        <VbIcon :name="item.icon" :size="19" />
        <span v-if="!collapsed" class="vb-nav-label">{{ item.label }}</span>
        <span v-if="!collapsed && item.badge" class="vb-nav-badge">{{ item.badge }}</span>
      </button>
    </nav>

    <!-- workspace section -->
    <div v-if="!collapsed" class="vb-side-section">
      <p class="vb-side-heading">Workspace</p>
      <button class="vb-nav-item vb-nav-sub" @click="$emit('navigate', 'library')">
        <VbIcon name="file" :size="17" />
        <span class="vb-nav-label">Documents</span>
        <span class="vb-nav-badge">{{ docCount }}</span>
      </button>
      <p v-if="!readyCount" class="vb-side-hint">Upload PDFs to build your second brain.</p>
    </div>

    <div class="vb-side-spacer" />

    <!-- bottom -->
    <nav class="vb-nav vb-nav-bottom">
      <button
        v-for="item in bottomNav" :key="item.id"
        class="vb-nav-item"
        :class="{ active: view === item.id }"
        :title="collapsed ? item.label : ''"
        :aria-current="view === item.id ? 'page' : undefined"
        @click="$emit('navigate', item.id)"
      >
        <VbIcon :name="item.icon" :size="19" />
        <span v-if="!collapsed" class="vb-nav-label">{{ item.label }}</span>
      </button>
      <button
        class="vb-nav-item vb-collapse-btn"
        @click="$emit('toggle-collapse')"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <VbIcon :name="collapsed ? 'chevRight' : 'chevLeft'" :size="18" />
        <span v-if="!collapsed" class="vb-nav-label">Collapse</span>
      </button>
    </nav>

    <!-- profile mini -->
    <button v-if="!collapsed" class="vb-profile-mini" @click="$emit('navigate', 'profile')">
      <span class="vb-avatar">{{ initials() }}</span>
      <span class="vb-profile-meta">
        <strong>{{ profile.name }}</strong>
        <small>{{ profile.workspace }}</small>
      </span>
    </button>
    <button v-else class="vb-avatar vb-avatar-collapsed" @click="$emit('navigate', 'profile')" :title="profile.name">
      {{ initials() }}
    </button>
  </aside>
</template>

<script setup>
import { computed } from 'vue';
import VbIcon from './VbIcon.vue';
import { useProfile } from '../composables/usePrefs.js';

defineProps({
  view: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
  docCount: { type: Number, default: 0 },
  readyCount: { type: Number, default: 0 },
  favCount: { type: Number, default: 0 },
});
defineEmits(['navigate', 'toggle-collapse']);

const { profile, initials } = useProfile();

const mainNav = computed(() => [
  { id: 'home', label: 'Home', icon: 'home' },
  { id: 'library', label: 'Library', icon: 'library' },
  { id: 'notebook', label: 'Notebook', icon: 'chat' },
  { id: 'favorites', label: 'Favorites', icon: 'star' },
  { id: 'recent', label: 'Recent', icon: 'clock' },
]);
const bottomNav = [
  { id: 'settings', label: 'Settings', icon: 'settings' },
];
</script>

<style scoped>
.vb-sidebar {
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  padding: 16px 12px;
  gap: 4px;
  height: 100vh;
  position: sticky; top: 0;
  transition: width var(--dur-med) var(--ease-out), background var(--dur-med);
  overflow-y: auto; overflow-x: hidden;
  flex-shrink: 0;
}
.vb-sidebar.collapsed { width: var(--sidebar-w-collapsed); align-items: center; padding: 16px 10px; }

.vb-logo {
  display: flex; align-items: center; gap: 11px;
  padding: 6px 8px 14px; border: 0; background: none; cursor: pointer;
  color: var(--text-1); text-align: left; width: 100%;
}
.vb-logo-mark {
  width: 40px; height: 40px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent); color: var(--accent-contrast);
  box-shadow: var(--shadow-sm);
  transition: background var(--dur-med);
}
.vb-logo-text { display: flex; flex-direction: column; line-height: 1.25; min-width: 0; }
.vb-logo-text strong { font-size: 15px; letter-spacing: -0.01em; }
.vb-logo-text small { font-size: 11px; color: var(--text-3); font-weight: 500; }

.vb-nav { display: flex; flex-direction: column; gap: 2px; }
.vb-nav-item {
  display: flex; align-items: center; gap: 11px;
  padding: 9px 11px; border-radius: var(--radius-md);
  border: 0; background: none; cursor: pointer;
  color: var(--text-2); font: 500 13.5px/1.2 var(--font-sans);
  transition: background var(--dur-fast), color var(--dur-fast);
  width: 100%; text-align: left; white-space: nowrap;
}
.vb-nav-item:hover { background: var(--hover-bg); color: var(--text-1); }
.vb-nav-item.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.vb-nav-item svg { flex-shrink: 0; }
.vb-nav-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.vb-nav-badge {
  font: 700 11px/1 var(--font-sans);
  background: var(--surface-3); color: var(--text-2);
  border-radius: 999px; padding: 4px 8px;
}
.vb-nav-item.active .vb-nav-badge { background: var(--accent); color: var(--accent-contrast); }

.vb-side-section { margin-top: 18px; padding: 0 4px; }
.vb-side-heading {
  font: 700 11px/1 var(--font-sans); letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-3); margin: 0 0 6px 8px;
}
.vb-nav-sub { padding: 8px 11px; font-size: 13px; }
.vb-side-hint { font-size: 12px; color: var(--text-3); margin: 8px 8px 0; line-height: 1.5; }

.vb-side-spacer { flex: 1; min-height: 12px; }
.vb-nav-bottom { border-top: 1px solid var(--border); padding-top: 10px; margin-top: 6px; }
.vb-collapse-btn { color: var(--text-3); }

.vb-profile-mini {
  display: flex; align-items: center; gap: 10px;
  margin-top: 10px; padding: 10px;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  background: var(--surface); cursor: pointer; width: 100%; text-align: left;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}
.vb-profile-mini:hover { border-color: var(--border-strong); box-shadow: var(--shadow-sm); }
.vb-avatar {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--accent-soft); color: var(--accent);
  font: 700 13px/1 var(--font-sans);
}
.vb-avatar-collapsed { margin-top: 10px; cursor: pointer; border: 0; width: 40px; height: 40px; }
.vb-profile-meta { display: flex; flex-direction: column; min-width: 0; line-height: 1.3; }
.vb-profile-meta strong { font-size: 13px; color: var(--text-1); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-profile-meta small { font-size: 11.5px; color: var(--text-3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.vb-sidebar.collapsed .vb-nav-item { justify-content: center; padding: 10px; }
.vb-sidebar.collapsed .vb-logo { justify-content: center; padding: 6px 0 14px; }
</style>
