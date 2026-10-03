<template>
  <div class="vb-page">
    <div class="vb-page-head vb-rise">
      <div>
        <h1>Settings</h1>
        <p>Tune Vector-Brain to the way you work. Everything is stored locally.</p>
      </div>
    </div>

    <!-- Appearance -->
    <section class="vb-card vb-settings-card">
      <h2><VbIcon name="sparkles" :size="17" /> Appearance</h2>

      <p class="vb-label">Theme</p>
      <div class="vb-theme-grid">
        <button
          v-for="t in THEMES" :key="t.id"
          class="vb-theme-card" :class="{ active: theme === t.id }"
          @click="theme = t.id"
          :aria-pressed="theme === t.id"
        >
          <span class="vb-theme-preview" :data-preview="t.id" />
          <strong>{{ t.label }}</strong>
          <small>{{ t.desc }}</small>
        </button>
      </div>

      <p class="vb-label" style="margin-top: 20px">Accent color</p>
      <div class="vb-accent-row">
        <button
          v-for="a in ACCENTS" :key="a.id"
          class="vb-accent-swatch" :class="{ active: accent === a.id }"
          :style="{ '--swatch': a.swatch }"
          @click="accent = a.id"
          :title="a.label" :aria-label="a.label + ' accent'" :aria-pressed="accent === a.id"
        >
          <VbIcon v-if="accent === a.id" name="check" :size="14" />
        </button>
      </div>

      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Interface density</p>
          <p class="vb-settings-row-desc">Compact fits more on screen; comfortable breathes.</p>
        </div>
        <div class="vb-segment">
          <button :class="{ active: density === 'comfortable' }" @click="density = 'comfortable'">Comfortable</button>
          <button :class="{ active: density === 'compact' }" @click="density = 'compact'">Compact</button>
        </div>
      </div>

      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Animations</p>
          <p class="vb-settings-row-desc">Auto follows your operating system preference.</p>
        </div>
        <div class="vb-segment">
          <button :class="{ active: reduceMotion === 'auto' }" @click="reduceMotion = 'auto'">Auto</button>
          <button :class="{ active: reduceMotion === 'full' }" @click="reduceMotion = 'full'">Full</button>
          <button :class="{ active: reduceMotion === 'reduced' }" @click="reduceMotion = 'reduced'">Reduced</button>
        </div>
      </div>
    </section>

    <!-- Notebook -->
    <section class="vb-card vb-settings-card">
      <h2><VbIcon name="chat" :size="17" /> Notebook</h2>

      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Retrieval depth (top-k)</p>
          <p class="vb-settings-row-desc">How many passages are considered per question.</p>
        </div>
        <select v-model.number="nb.topK" class="vb-select vb-select-sm" @change="saveNb" aria-label="Retrieval depth">
          <option :value="3">3 passages</option>
          <option :value="6">6 passages</option>
          <option :value="10">10 passages</option>
          <option :value="15">15 passages</option>
        </select>
      </div>

      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Citation display</p>
          <p class="vb-settings-row-desc">How sources appear in answers.</p>
        </div>
        <div class="vb-segment">
          <button :class="{ active: nb.citationStyle === 'numbered' }" @click="setNb('citationStyle', 'numbered')">Numbered [1]</button>
          <button :class="{ active: nb.citationStyle === 'detailed' }" @click="setNb('citationStyle', 'detailed')">Detailed</button>
        </div>
      </div>

      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Streaming responses</p>
          <p class="vb-settings-row-desc">Show tokens as they arrive (recommended).</p>
        </div>
        <button
          class="vb-switch" :class="{ on: nb.streaming }" role="switch" :aria-checked="nb.streaming"
          @click="setNb('streaming', !nb.streaming)" aria-label="Streaming responses"
        ><span class="vb-switch-knob" /></button>
      </div>
    </section>

    <!-- Library -->
    <section class="vb-card vb-settings-card">
      <h2><VbIcon name="library" :size="17" /> Library</h2>
      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Default view</p>
          <p class="vb-settings-row-desc">Grid or list when opening the Library.</p>
        </div>
        <div class="vb-segment">
          <button :class="{ active: lib.view === 'grid' }" @click="setLib('view', 'grid')">Grid</button>
          <button :class="{ active: lib.view === 'list' }" @click="setLib('view', 'list')">List</button>
        </div>
      </div>
      <div class="vb-settings-row">
        <div>
          <p class="vb-settings-row-title">Default sorting</p>
          <p class="vb-settings-row-desc">How documents are ordered.</p>
        </div>
        <select v-model="lib.sort" class="vb-select vb-select-sm" @change="saveLib" aria-label="Default sorting">
          <option value="recent">Recently added</option>
          <option value="name">Name</option>
          <option value="size">Size</option>
          <option value="pages">Pages</option>
        </select>
      </div>
    </section>

    <!-- About -->
    <section class="vb-card vb-settings-card">
      <h2><VbIcon name="info" :size="17" /> About</h2>
      <dl class="vb-about">
        <div><dt>Vector-Brain</dt><dd>v2.0 · Notebook LLM Lite</dd></div>
        <div><dt>Pipeline</dt><dd>PDFs → Docling → 384-dim embeddings → PostgreSQL + pgvector → Groq</dd></div>
        <div><dt>Frontend</dt><dd>Vue 3 · dependency-free UI</dd></div>
        <div><dt>Backend</dt><dd>FastAPI · Docling · sentence-transformers · pgvector</dd></div>
      </dl>
    </section>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';
import VbIcon from '../components/VbIcon.vue';
import { useTheme } from '../composables/useTheme.js';
import { usePrefs } from '../composables/usePrefs.js';

const { theme, accent, density, reduceMotion, THEMES, ACCENTS } = useTheme();
const { notebookPrefs, libraryPrefs, saveNotebook, saveLibrary } = usePrefs();

const nb = reactive({ ...notebookPrefs.value });
const lib = reactive({ ...libraryPrefs.value });
watch(notebookPrefs, (v) => Object.assign(nb, v), { deep: true });
watch(libraryPrefs, (v) => Object.assign(lib, v), { deep: true });

function saveNb() { saveNotebook({ ...nb }); }
function setNb(k, v) { nb[k] = v; saveNb(); }
function saveLib() { saveLibrary({ ...lib }); }
function setLib(k, v) { lib[k] = v; saveLib(); }
</script>

<style scoped>
.vb-page { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
.vb-page-head h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px; }
.vb-page-head p { font-size: 13.5px; color: var(--text-2); margin: 0; }
.vb-settings-card { padding: 24px; }
.vb-settings-card h2 { display: flex; align-items: center; gap: 9px; font-size: 16px; font-weight: 700; margin: 0 0 18px; color: var(--accent); }
.vb-label { margin-top: 4px; }

.vb-theme-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.vb-theme-card {
  border: 2px solid var(--border); border-radius: var(--radius-md); background: var(--surface-2);
  padding: 10px; cursor: pointer; text-align: left; display: flex; flex-direction: column; gap: 6px;
  transition: border-color var(--dur-fast), transform var(--dur-fast);
}
.vb-theme-card:hover { transform: translateY(-1px); }
.vb-theme-card.active { border-color: var(--accent); }
.vb-theme-card strong { font-size: 13px; }
.vb-theme-card small { font-size: 11px; color: var(--text-3); line-height: 1.4; }
.vb-theme-preview { height: 44px; border-radius: 8px; border: 1px solid var(--border); }
.vb-theme-preview[data-preview="light"] { background: linear-gradient(135deg, #ffffff 60%, #f7f6f3 60%); }
.vb-theme-preview[data-preview="dark"] { background: linear-gradient(135deg, #171a20 60%, #101216 60%); }
.vb-theme-preview[data-preview="midnight"] { background: linear-gradient(135deg, #171b38 60%, #0a0d1f 60%); }
.vb-theme-preview[data-preview="contrast"] { background: linear-gradient(135deg, #ffffff 50%, #000000 50%); }

.vb-accent-row { display: flex; gap: 10px; }
.vb-accent-swatch {
  width: 40px; height: 40px; border-radius: 50%; border: 2px solid transparent;
  background: var(--swatch); cursor: pointer; color: #fff;
  display: flex; align-items: center; justify-content: center;
  transition: transform var(--dur-fast), border-color var(--dur-fast);
}
.vb-accent-swatch:hover { transform: scale(1.08); }
.vb-accent-swatch.active { border-color: var(--text-1); box-shadow: 0 0 0 3px var(--accent-soft); }

.vb-settings-row {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 16px 0; border-top: 1px solid var(--border); margin-top: 16px;
}
.vb-settings-row:first-of-type { border-top: 0; }
.vb-settings-row-title { font-size: 14px; font-weight: 600; margin: 0 0 3px; }
.vb-settings-row-desc { font-size: 12.5px; color: var(--text-3); margin: 0; }

.vb-segment { display: flex; background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 3px; gap: 2px; }
.vb-segment button {
  border: 0; background: none; cursor: pointer; padding: 8px 14px; border-radius: 7px;
  font: 600 12.5px var(--font-sans); color: var(--text-2); white-space: nowrap;
}
.vb-segment button.active { background: var(--surface); color: var(--text-1); box-shadow: var(--shadow-sm); }

.vb-switch {
  width: 46px; height: 26px; border-radius: 999px; border: 0; cursor: pointer;
  background: var(--surface-3); position: relative; transition: background var(--dur-fast);
  flex-shrink: 0;
}
.vb-switch.on { background: var(--accent); }
.vb-switch-knob {
  position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%;
  background: #fff; box-shadow: var(--shadow-sm); transition: transform var(--dur-fast) var(--ease-out);
}
.vb-switch.on .vb-switch-knob { transform: translateX(20px); }

.vb-select-sm { width: auto; padding: 8px 10px; font-size: 13px; }
.vb-about { margin: 0; display: flex; flex-direction: column; gap: 10px; }
.vb-about div { display: grid; grid-template-columns: 110px 1fr; gap: 12px; font-size: 13px; }
.vb-about dt { color: var(--text-3); font-weight: 600; }
.vb-about dd { margin: 0; color: var(--text-1); }

@media (max-width: 640px) {
  .vb-theme-grid { grid-template-columns: repeat(2, 1fr); }
  .vb-settings-row { flex-direction: column; align-items: flex-start; }
}
</style>
