<template>
  <div class="vb-page">
    <div class="vb-page-head vb-rise">
      <div>
        <h1>Profile</h1>
        <p>Your local identity in Vector-Brain. No account, no tracking — just preferences.</p>
      </div>
    </div>

    <section class="vb-card vb-profile-card">
      <div class="vb-profile-top">
        <div class="vb-profile-avatar">{{ initials() }}</div>
        <div>
          <h2>{{ form.name || 'Researcher' }}</h2>
          <p>{{ form.workspace || 'My Second Brain' }}</p>
        </div>
      </div>

      <div class="vb-form-grid">
        <div>
          <label class="vb-label" for="pf-name">Display name</label>
          <input id="pf-name" v-model="form.name" class="vb-input" type="text" placeholder="Ada Lovelace" maxlength="60" />
        </div>
        <div>
          <label class="vb-label" for="pf-email">Email <span class="vb-optional">(optional, local only)</span></label>
          <input id="pf-email" v-model="form.email" class="vb-input" type="email" placeholder="you@example.com" maxlength="120" />
        </div>
        <div class="vb-form-full">
          <label class="vb-label" for="pf-workspace">Workspace name</label>
          <input id="pf-workspace" v-model="form.workspace" class="vb-input" type="text" placeholder="My Second Brain" maxlength="60" />
        </div>
      </div>

      <div class="vb-profile-actions">
        <button class="vb-btn vb-btn-primary" @click="saveProfile" :disabled="!dirty">Save changes</button>
        <span v-if="savedTick" class="vb-saved"><VbIcon name="check" :size="14" /> Saved</span>
      </div>
    </section>

    <section class="vb-card vb-profile-card">
      <h2 class="vb-card-title">Your activity</h2>
      <div class="vb-activity-grid">
        <div class="vb-activity"><strong>{{ documents.length }}</strong><span>documents</span></div>
        <div class="vb-activity"><strong>{{ formatNumber(totalChunks) }}</strong><span>chunks indexed</span></div>
        <div class="vb-activity"><strong>{{ recentQuestions.length }}</strong><span>questions asked</span></div>
        <div class="vb-activity"><strong>{{ conversations.length }}</strong><span>saved chats</span></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue';
import VbIcon from '../components/VbIcon.vue';
import { formatNumber } from '../utils/format.js';
import { useProfile, useRecents, useChatHistory } from '../composables/usePrefs.js';
import { useToasts } from '../composables/useToasts.js';

const props = defineProps({
  documents: { type: Array, default: () => [] },
  totalChunks: { type: Number, default: 0 },
});

const { profile, save, initials } = useProfile();
const { recentQuestions } = useRecents();
const { conversations } = useChatHistory();
const { success } = useToasts();

const form = reactive({ name: profile.value.name, email: profile.value.email, workspace: profile.value.workspace });
const dirty = ref(false);
const savedTick = ref(false);

watch(form, () => { dirty.value = true; savedTick.value = false; });

function saveProfile() {
  save({ name: form.name.trim() || 'Researcher', email: form.email.trim(), workspace: form.workspace.trim() || 'My Second Brain' });
  dirty.value = false;
  savedTick.value = true;
  success('Profile saved.');
  setTimeout(() => { savedTick.value = false; }, 2500);
}
</script>

<style scoped>
.vb-page { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }
.vb-page-head h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0 0 4px; }
.vb-page-head p { font-size: 13.5px; color: var(--text-2); margin: 0; }
.vb-profile-card { padding: 26px; }
.vb-profile-top { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.vb-profile-avatar {
  width: 68px; height: 68px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent); color: var(--accent-contrast);
  font: 800 24px/1 var(--font-sans);
}
.vb-profile-top h2 { margin: 0 0 4px; font-size: 20px; font-weight: 800; letter-spacing: -0.01em; }
.vb-profile-top p { margin: 0; font-size: 13.5px; color: var(--text-2); }
.vb-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.vb-form-full { grid-column: 1 / -1; }
.vb-optional { font-weight: 400; color: var(--text-3); }
.vb-profile-actions { display: flex; align-items: center; gap: 12px; margin-top: 20px; }
.vb-saved { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--success); }
.vb-card-title { font-size: 16px; font-weight: 700; margin: 0 0 16px; }
.vb-activity-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.vb-activity {
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 16px; display: flex; flex-direction: column; gap: 4px; text-align: center;
}
.vb-activity strong { font-size: 22px; font-weight: 800; letter-spacing: -0.02em; }
.vb-activity span { font-size: 12px; color: var(--text-3); }
@media (max-width: 640px) {
  .vb-form-grid { grid-template-columns: 1fr; }
  .vb-activity-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
