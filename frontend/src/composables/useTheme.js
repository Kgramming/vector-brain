/**
 * Theme / accent / density / motion preferences.
 * Persisted to localStorage; applied as data-* attributes on <html>.
 */
import { ref, watch } from 'vue';

const THEMES = [
  { id: 'light', label: 'Light', desc: 'Clean professional light theme' },
  { id: 'dark', label: 'Dark', desc: 'Modern dark AI workspace' },
  { id: 'midnight', label: 'Midnight', desc: 'Deep blue research environment' },
  { id: 'contrast', label: 'High Contrast', desc: 'Accessibility-focused' },
];

const ACCENTS = [
  { id: 'violet', label: 'Violet', swatch: '#7c3aed' },
  { id: 'blue', label: 'Blue', swatch: '#2563eb' },
  { id: 'cyan', label: 'Cyan', swatch: '#0891b2' },
  { id: 'green', label: 'Green', swatch: '#16a34a' },
  { id: 'orange', label: 'Orange', swatch: '#ea580c' },
  { id: 'rose', label: 'Rose', swatch: '#e11d48' },
];

function load(key, fallback) {
  try {
    const v = localStorage.getItem('vb:' + key);
    return v !== null ? v : fallback;
  } catch { return fallback; }
}

const theme = ref(load('theme', 'light'));
const accent = ref(load('accent', 'violet'));
const density = ref(load('density', 'comfortable'));
const reduceMotion = ref(load('motion', 'auto')); // auto | reduced | full

function apply() {
  const root = document.documentElement;
  // "auto" follows the OS setting; explicit choices override it.
  const osReduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const motion = reduceMotion.value === 'auto' ? (osReduced ? 'reduced' : 'full') : reduceMotion.value;
  root.dataset.theme = theme.value;
  root.dataset.accent = accent.value;
  root.dataset.density = density.value;
  root.dataset.motion = motion;
  try {
    localStorage.setItem('vb:theme', theme.value);
    localStorage.setItem('vb:accent', accent.value);
    localStorage.setItem('vb:density', density.value);
    localStorage.setItem('vb:motion', reduceMotion.value);
  } catch { /* private mode */ }
}

watch([theme, accent, density, reduceMotion], apply, { immediate: false });

export function useTheme() {
  return { theme, accent, density, reduceMotion, THEMES, ACCENTS, apply };
}
