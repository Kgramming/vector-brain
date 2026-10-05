/** Small formatting helpers. */

export function formatBytes(bytes) {
  if (bytes == null || isNaN(bytes)) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  let n = Number(bytes), u = 0;
  while (n >= 1024 && u < units.length - 1) { n /= 1024; u++; }
  return `${n >= 100 ? Math.round(n) : n.toFixed(1)} ${units[u]}`;
}

export function formatNumber(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US');
}

export function timeAgo(iso) {
  if (!iso) return '';
  const t = new Date(iso).getTime();
  const s = Math.max(1, Math.floor((Date.now() - t) / 1000));
  if (s < 60) return 'just now';
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function shortName(name, max = 28) {
  const t = name || 'document';
  return t.length > max ? t.slice(0, max - 1) + '…' : t;
}

export function relevanceLabel(similarity) {
  const s = Number(similarity);
  if (s >= 0.75) return 'high';
  if (s >= 0.5) return 'medium';
  return 'low';
}

export function pageLabel(pageStart, pageEnd) {
  if (!pageStart) return '';
  if (pageEnd && pageEnd !== pageStart) return `pp. ${pageStart}–${pageEnd}`;
  return `p. ${pageStart}`;
}

/**
 * Extract the set of citation ranks (e.g. [1], [3]) cited in an answer.
 * Used to keep the Sources panel consistent with the citations the model
 * actually emitted — never show a source the answer didn't cite.
 */
export function citedRanks(text) {
  const ranks = new Set();
  if (!text) return ranks;
  const re = /\[(\d+)\]/g;
  let m;
  while ((m = re.exec(text)) !== null) ranks.add(Number(m[1]));
  return ranks;
}

/**
 * Keep only the sources whose rank was cited in the answer text.
 * The Sources panel must correspond exactly to the emitted citations.
 */
export function filterSourcesToCited(sources, answerText) {
  const cited = citedRanks(answerText);
  return (sources || []).filter(s => cited.has(s.rank));
}
