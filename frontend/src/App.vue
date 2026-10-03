<template>
  <div class="vb-app">
    <!-- desktop sidebar -->
    <AppSidebar
      v-if="!isMobile"
      :view="view" :collapsed="sidebarCollapsed"
      :doc-count="documents.length" :ready-count="readyDocs.length"
      @navigate="go" @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
    />

    <!-- mobile drawer -->
    <div v-if="isMobile && drawerOpen" class="vb-drawer-backdrop" @click="drawerOpen = false" />
    <transition name="vb-drawer">
      <div v-if="isMobile && drawerOpen" class="vb-drawer" role="dialog" aria-modal="true" aria-label="Navigation">
        <AppSidebar
          :view="view"
          :doc-count="documents.length" :ready-count="readyDocs.length"
          @navigate="(v) => { go(v); drawerOpen = false; }" @toggle-collapse="drawerOpen = false"
        />
      </div>
    </transition>

    <div class="vb-main">
      <!-- mobile topbar -->
      <header v-if="isMobile" class="vb-topbar">
        <button class="vb-btn vb-btn-ghost vb-btn-icon" @click="drawerOpen = true" aria-label="Open navigation">
          <VbIcon name="menu" :size="20" />
        </button>
        <span class="vb-topbar-logo"><VbIcon name="brain" :size="20" /> Vector-Brain</span>
        <button class="vb-btn vb-btn-primary vb-btn-sm" @click="uploadOpen = true" aria-label="Upload documents">
          <VbIcon name="plus" :size="15" />
        </button>
      </header>

      <div v-if="backendDown" class="vb-banner" role="alert">
        <VbIcon name="alert" :size="15" />
        Backend unreachable — start it with <code>uvicorn app.main:app --port 8000</code> in <code>backend/</code>.
      </div>
      <div v-else-if="health?.groq_mode === 'mock' && !mockDismissed" class="vb-banner vb-banner-warn">
        <VbIcon name="info" :size="15" />
        <span>Mock mode — set <code>GROQ_API_KEY</code> in <code>backend/.env</code> for live answers.</span>
        <button class="vb-banner-x" @click="mockDismissed = true" aria-label="Dismiss"><VbIcon name="x" :size="13" /></button>
      </div>

      <main class="vb-content" :key="view">
        <HomeView
          v-if="view === 'home'"
          :documents="documents" :health="health" :loading="loading"
          :total-pages="totalPages" :total-chunks="totalChunks"
          @upload="uploadOpen = true" @navigate="go"
          @open-doc="openInNotebook" @delete-doc="go('library')"
          @toggle-fav="toggleFav" @ask-again="askAgain"
        />
        <LibraryView
          v-else-if="view === 'library'"
          :documents="documents" :loading="loading"
          :total-pages="totalPages" :total-chunks="totalChunks"
          @upload="uploadOpen = true" @open-doc="openInNotebook"
          @toggle-fav="toggleFav" @refresh="refresh"
        />
        <NotebookView
          v-else-if="view === 'notebook'"
          :documents="documents"
          :preset-doc-ids="notebookPreset.docIds"
          :preset-question="notebookPreset.question"
          @upload="uploadOpen = true"
        />
        <FavoritesView
          v-else-if="view === 'favorites'"
          :documents="documents"
          @navigate="go" @open-doc="openInNotebook"
          @delete-doc="go('library')" @toggle-fav="toggleFav"
        />
        <RecentView
          v-else-if="view === 'recent'"
          :documents="documents"
          @navigate="go" @open-doc="openInNotebook"
          @delete-doc="go('library')" @toggle-fav="toggleFav" @ask-again="askAgain"
        />
        <SettingsView v-else-if="view === 'settings'" />
        <ProfileView
          v-else-if="view === 'profile'"
          :documents="documents" :total-chunks="totalChunks"
        />
      </main>
    </div>

    <UploadModal v-if="uploadOpen" :max-mb="50" @close="uploadOpen = false" @uploaded="refresh" />
    <Toasts />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import VbIcon from './components/VbIcon.vue';
import AppSidebar from './components/AppSidebar.vue';
import Toasts from './components/Toasts.vue';
import UploadModal from './components/UploadModal.vue';
import HomeView from './views/HomeView.vue';
import LibraryView from './views/LibraryView.vue';
import NotebookView from './views/NotebookView.vue';
import FavoritesView from './views/FavoritesView.vue';
import RecentView from './views/RecentView.vue';
import SettingsView from './views/SettingsView.vue';
import ProfileView from './views/ProfileView.vue';
import { useLibrary } from './composables/useLibrary.js';
import { useFavorites, useRecents } from './composables/usePrefs.js';

const view = ref('home');
const uploadOpen = ref(false);
const drawerOpen = ref(false);
const sidebarCollapsed = ref(false);
const mockDismissed = ref(false);
const isMobile = ref(false);
const notebookPreset = ref({ docIds: [], question: '' });

const { documents, health, loading, backendDown, readyDocs, totalPages, totalChunks, refresh, startPolling } = useLibrary();
const { toggle: toggleFav } = useFavorites();
const { touchDoc } = useRecents();

function go(v) {
  view.value = v;
  // clear notebook presets when leaving so re-entry is clean
  if (v !== 'notebook') notebookPreset.value = { docIds: [], question: '' };
}

function openInNotebook(doc) {
  touchDoc(doc.id);
  notebookPreset.value = { docIds: [doc.id], question: '' };
  view.value = 'notebook';
}

function askAgain(q) {
  notebookPreset.value = { docIds: [], question: q };
  view.value = 'notebook';
}

function checkMobile() {
  isMobile.value = window.innerWidth < 900;
  if (!isMobile.value) drawerOpen.value = false;
}

onMounted(() => {
  checkMobile();
  window.addEventListener('resize', checkMobile);
  refresh();
  startPolling();
});
onUnmounted(() => window.removeEventListener('resize', checkMobile));
</script>

<style>
.vb-app { display: flex; height: 100vh; overflow: hidden; }
.vb-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.vb-content { flex: 1; overflow-y: auto; padding: 28px 32px 48px; }
.vb-content > * { animation: vb-rise var(--dur-med) var(--ease-out); }

.vb-topbar {
  display: flex; align-items: center; justify-content: space-between;
  height: var(--topbar-h); padding: 0 12px; flex-shrink: 0;
  background: var(--topbar-bg); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.vb-topbar-logo { display: flex; align-items: center; gap: 8px; font-weight: 800; font-size: 16px; color: var(--accent); }

.vb-drawer-backdrop { position: fixed; inset: 0; z-index: 40; background: var(--overlay); }
.vb-drawer { position: fixed; top: 0; bottom: 0; left: 0; z-index: 50; box-shadow: var(--shadow-lg); }
.vb-drawer .vb-sidebar { height: 100%; }
.vb-drawer-enter-active, .vb-drawer-leave-active { transition: transform var(--dur-med) var(--ease-out); }
.vb-drawer-enter-from, .vb-drawer-leave-to { transform: translateX(-100%); }

.vb-banner {
  display: flex; align-items: center; gap: 10px; justify-content: center;
  padding: 9px 16px; font-size: 13px;
  background: var(--danger-soft); color: var(--danger); border-bottom: 1px solid var(--border);
}
.vb-banner-warn { background: var(--warning-soft); color: var(--warning); }
.vb-banner code { font-family: var(--font-mono); font-size: 12px; background: rgb(0 0 0 / 0.08); padding: 1px 6px; border-radius: 6px; }
.vb-banner-x { border: 0; background: none; cursor: pointer; color: inherit; padding: 4px; border-radius: 6px; display: inline-flex; }

@media (max-width: 900px) {
  .vb-content { padding: 18px 16px 40px; }
}
</style>
