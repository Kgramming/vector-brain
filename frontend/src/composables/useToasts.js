/** Minimal toast notification system. */
import { ref } from 'vue';

const toasts = ref([]);
let nextId = 1;

export function useToasts() {
  function push(message, kind = 'info', ms = 4200) {
    const id = nextId++;
    toasts.value.push({ id, message, kind, leaving: false });
    setTimeout(() => dismiss(id), ms);
    return id;
  }
  function dismiss(id) {
    const t = toasts.value.find(t => t.id === id);
    if (!t) return;
    t.leaving = true;
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id);
    }, 180);
  }
  const success = (m, ms) => push(m, 'success', ms);
  const error = (m, ms) => push(m, 'error', ms);
  const info = (m, ms) => push(m, 'info', ms);
  return { toasts, push, dismiss, success, error, info };
}
