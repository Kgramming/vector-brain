/**
 * Local user preferences: profile, favorites, recents, chat history.
 * Everything is client-side (no auth in this app) and persisted to localStorage.
 */
import { ref } from 'vue';

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem('vb:' + key);
    return raw ? JSON.parse(raw) : fallback;
  } catch { return fallback; }
}
function saveJSON(key, value) {
  try { localStorage.setItem('vb:' + key, JSON.stringify(value)); } catch { /* ignore */ }
}

/* ------------------------------- profile -------------------------------- */

const profile = ref({
  name: loadJSON('profile:name', 'Researcher'),
  email: loadJSON('profile:email', ''),
  workspace: loadJSON('profile:workspace', 'My Second Brain'),
  ...loadJSON('profile', {}),
});

export function useProfile() {
  function save(p) {
    profile.value = { ...profile.value, ...p };
    saveJSON('profile', profile.value);
  }
  function initials() {
    const n = (profile.value.name || 'R').trim();
    return n.split(/\s+/).slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('') || 'R';
  }
  return { profile, save, initials };
}

/* ------------------------------ favorites -------------------------------- */

const favorites = ref(loadJSON('favorites', [])); // document ids

export function useFavorites() {
  function isFav(id) { return favorites.value.includes(id); }
  function toggle(id) {
    favorites.value = isFav(id)
      ? favorites.value.filter(f => f !== id)
      : [...favorites.value, id];
    saveJSON('favorites', favorites.value);
  }
  return { favorites, isFav, toggle };
}

/* -------------------------------- recents --------------------------------- */

const recentDocs = ref(loadJSON('recentDocs', [])); // [{id, at}]
const recentQuestions = ref(loadJSON('recentQuestions', [])); // [{q, at, declined}]

export function useRecents() {
  function touchDoc(id) {
    recentDocs.value = [{ id, at: Date.now() },
      ...recentDocs.value.filter(r => r.id !== id)].slice(0, 20);
    saveJSON('recentDocs', recentDocs.value);
  }
  function pushQuestion(q, declined = false) {
    recentQuestions.value = [{ q, at: Date.now(), declined },
      ...recentQuestions.value.filter(r => r.q !== q)].slice(0, 20);
    saveJSON('recentQuestions', recentQuestions.value);
  }
  function clearQuestions() {
    recentQuestions.value = [];
    saveJSON('recentQuestions', recentQuestions.value);
  }
  return { recentDocs, recentQuestions, touchDoc, pushQuestion, clearQuestions };
}

/* ------------------------------ chat history ------------------------------ */

const conversations = ref(loadJSON('conversations', [])); // [{id, title, at, messages: [{role, content, sources, declined}]}]

export function useChatHistory() {
  function saveConversation(conv) {
    conversations.value = [conv, ...conversations.value.filter(c => c.id !== conv.id)].slice(0, 30);
    saveJSON('conversations', conversations.value);
  }
  function removeConversation(id) {
    conversations.value = conversations.value.filter(c => c.id !== id);
    saveJSON('conversations', conversations.value);
  }
  function clearAll() {
    conversations.value = [];
    saveJSON('conversations', conversations.value);
  }
  return { conversations, saveConversation, removeConversation, clearAll };
}

/* --------------------------- notebook settings ---------------------------- */

const notebookPrefs = ref({
  defaultScope: loadJSON('prefs:scope', 'all'), // 'all' | 'favorites' | 'recent'
  citationStyle: loadJSON('prefs:citationStyle', 'numbered'), // numbered | detailed
  streaming: loadJSON('prefs:streaming', true),
  topK: loadJSON('prefs:topK', 6),
  ...loadJSON('prefs:notebook', {}),
});

const libraryPrefs = ref({
  view: loadJSON('prefs:view', 'grid'), // grid | list
  sort: loadJSON('prefs:sort', 'recent'), // recent | name | size | pages
  ...loadJSON('prefs:library', {}),
});

export function usePrefs() {
  function saveNotebook(p) {
    notebookPrefs.value = { ...notebookPrefs.value, ...p };
    saveJSON('prefs:notebook', notebookPrefs.value);
  }
  function saveLibrary(p) {
    libraryPrefs.value = { ...libraryPrefs.value, ...p };
    saveJSON('prefs:library', libraryPrefs.value);
  }
  return { notebookPrefs, libraryPrefs, saveNotebook, saveLibrary };
}
