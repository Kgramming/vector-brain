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

    <!-- conversations -->
    <div v-if="!collapsed" class="vb-chats">
      <button class="vb-new-chat" @click="$emit('new-chat')">
        <VbIcon name="plus" :size="15" />
        <span class="vb-nav-label">New chat</span>
      </button>
      <p class="vb-side-heading">Recent chats</p>
      <div class="vb-chat-list">
        <div
          v-for="c in conversations" :key="c.id"
          class="vb-chat-item"
          :class="{ active: c.id === currentConvoId }"
        >
          <!-- normal row -->
          <template v-if="deletingId !== c.id">
            <button
              v-if="renamingId !== c.id"
              class="vb-chat-open"
              @click="$emit('open-chat', c)"
              :title="c.title"
            >
              <VbIcon name="chat" :size="15" class="vb-chat-ico" />
              <span class="vb-chat-title">{{ c.title || 'Conversation' }}</span>
            </button>
            <input
              v-else
              ref="renameInput"
              v-model="renameText"
              class="vb-chat-rename"
              aria-label="Rename conversation"
              @keydown.enter="commitRename(c)"
              @keydown.escape="renamingId = null"
              @blur="commitRename(c)"
              @click.stop
            />
            <button
              v-if="renamingId !== c.id"
              class="vb-chat-menu-btn"
              :aria-expanded="menuFor === c.id"
              aria-label="Conversation options"
              title="Options"
              @click.stop="menuFor = menuFor === c.id ? null : c.id"
            >
              <VbIcon name="dots" :size="15" />
            </button>
            <div v-if="menuFor === c.id && renamingId !== c.id" class="vb-chat-menu" role="menu">
              <button role="menuitem" @click="startRename(c)"><VbIcon name="pencil" :size="14" /> Rename</button>
              <button role="menuitem" class="danger" @click="askDelete(c)"><VbIcon name="trash" :size="14" /> Delete</button>
            </div>
          </template>
          <!-- delete confirm -->
          <div v-else class="vb-chat-del">
            <span class="vb-chat-del-text">Delete this chat?</span>
            <div class="vb-chat-del-actions">
              <button class="vb-btn vb-btn-sm vb-chat-del-yes" @click.stop="$emit('delete-chat', c.id); deletingId = null">Delete</button>
              <button class="vb-btn vb-btn-ghost vb-btn-sm" @click.stop="deletingId = null">Cancel</button>
            </div>
          </div>
        </div>
        <p v-if="!conversations.length" class="vb-side-hint">No conversations yet — ask something in Notebook.</p>
      </div>
    </div>
    <div v-if="menuFor" class="vb-menu-backdrop" @click="menuFor = null" />

    <div v-if="collapsed" class="vb-side-spacer" />

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
import { computed, ref, nextTick } from 'vue';
import VbIcon from './VbIcon.vue';
import { useProfile, useChatHistory } from '../composables/usePrefs.js';

defineProps({
  view: { type: String, required: true },
  collapsed: { type: Boolean, default: false },
  docCount: { type: Number, default: 0 },
  readyCount: { type: Number, default: 0 },
  favCount: { type: Number, default: 0 },
});
defineEmits(['navigate', 'toggle-collapse', 'new-chat', 'open-chat', 'delete-chat']);

const { profile, initials } = useProfile();
const { conversations, currentConvoId, renameConversation } = useChatHistory();

const menuFor = ref(null);
const renamingId = ref(null);
const renameText = ref('');
const renameInput = ref(null);
const deletingId = ref(null);
let renameCommitted = false;

function startRename(c) {
  menuFor.value = null;
  deletingId.value = null;
  renamingId.value = c.id;
  renameText.value = c.title || '';
  renameCommitted = false;
  nextTick(() => {
    const el = Array.isArray(renameInput.value) ? renameInput.value[0] : renameInput.value;
    el?.focus();
    el?.select();
  });
}
function commitRename(c) {
  if (renameCommitted || renamingId.value !== c.id) return;
  renameCommitted = true;
  const t = renameText.value.trim();
  if (t && t !== c.title) renameConversation(c.id, t);
  renamingId.value = null;
}
function askDelete(c) {
  menuFor.value = null;
  renamingId.value = null;
  deletingId.value = c.id;
}

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

/* ---- recent chats ---- */
.vb-chats {
  flex: 1; min-height: 0;
  display: flex; flex-direction: column;
  margin-top: 16px;
}
.vb-new-chat {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 10px 12px; margin-bottom: 14px;
  border: 1px solid var(--border); border-radius: var(--radius-md);
  background: var(--surface); color: var(--text-1);
  font: 600 13.5px/1.2 var(--font-sans); cursor: pointer; text-align: left;
  transition: border-color var(--dur-fast), color var(--dur-fast), box-shadow var(--dur-fast);
  flex-shrink: 0;
}
.vb-new-chat:hover { border-color: var(--accent-border); color: var(--accent); box-shadow: var(--shadow-sm); }
.vb-new-chat svg { flex-shrink: 0; }
.vb-chats .vb-side-heading { margin-bottom: 4px; }
.vb-chat-list {
  flex: 1; min-height: 0; overflow-y: auto;
  display: flex; flex-direction: column; gap: 2px;
  margin: 0 -4px; padding: 2px 4px 8px;
}
.vb-chat-item {
  position: relative; display: flex; align-items: center;
  border-radius: var(--radius-md);
  transition: background var(--dur-fast);
}
.vb-chat-item:hover { background: var(--hover-bg); }
.vb-chat-item.active { background: var(--accent-soft); }
.vb-chat-open {
  flex: 1; min-width: 0; display: flex; align-items: center; gap: 9px;
  padding: 8px 6px 8px 10px; border: 0; background: none; cursor: pointer;
  color: var(--text-2); font: 500 13px/1.35 var(--font-sans); text-align: left;
}
.vb-chat-item.active .vb-chat-open { color: var(--accent); font-weight: 600; }
.vb-chat-ico { flex-shrink: 0; opacity: 0.7; }
.vb-chat-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vb-chat-menu-btn {
  flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; margin-right: 4px;
  border: 0; border-radius: 8px; background: none; cursor: pointer; color: var(--text-3);
  opacity: 0; transition: opacity var(--dur-fast), background var(--dur-fast), color var(--dur-fast);
}
.vb-chat-item:hover .vb-chat-menu-btn,
.vb-chat-item.active .vb-chat-menu-btn,
.vb-chat-menu-btn[aria-expanded="true"] { opacity: 1; }
.vb-chat-menu-btn:hover { background: var(--surface-3); color: var(--text-1); }
.vb-chat-menu {
  position: absolute; right: 4px; top: calc(100% - 4px); z-index: 30;
  min-width: 140px; padding: 4px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column;
}
.vb-chat-menu button {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px; border: 0; border-radius: 8px; background: none; cursor: pointer;
  color: var(--text-2); font: 500 13px var(--font-sans); text-align: left; width: 100%;
}
.vb-chat-menu button:hover { background: var(--hover-bg); color: var(--text-1); }
.vb-chat-menu button.danger { color: var(--danger); }
.vb-chat-menu button.danger:hover { background: var(--danger-soft); }
.vb-menu-backdrop { position: fixed; inset: 0; z-index: 20; }
.vb-chat-rename {
  flex: 1; min-width: 0; margin: 4px 4px 4px 10px; padding: 6px 8px;
  border: 1px solid var(--accent); border-radius: 8px;
  background: var(--input-bg); color: var(--text-1);
  font: 500 13px var(--font-sans);
}
.vb-chat-rename:focus { outline: none; box-shadow: 0 0 0 3px var(--accent-soft); }
.vb-chat-del { flex: 1; min-width: 0; padding: 8px 10px; display: flex; flex-direction: column; gap: 8px; }
.vb-chat-del-text { font-size: 12.5px; font-weight: 600; color: var(--text-1); }
.vb-chat-del-actions { display: flex; gap: 6px; }
.vb-chat-del-yes { background: var(--danger); border-color: var(--danger); color: #fff; }
.vb-chat-del-yes:hover { filter: brightness(0.95); }
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
