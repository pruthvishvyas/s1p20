export const CURRENCY = '$';
const num = (v) => (v === null || v === undefined || v === '' ? NaN : Number(v));

export function fmtMoney(v, dec = 0) {
  const n = num(v);
  if (!Number.isFinite(n)) return '—';
  return (n < 0 ? '-' : '') + CURRENCY + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
export function fmtPct(v, dec = 1) {
  const n = num(v);
  return Number.isFinite(n) ? n.toFixed(dec) + '%' : '—';
}
export function fmtInt(v) {
  const n = num(v);
  return Number.isFinite(n) ? Math.round(n).toLocaleString('en-US') : '—';
}
export function fmtCompact(v) {
  const n = num(v);
  if (!Number.isFinite(n)) return '';
  const a = Math.abs(n);
  if (a >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (a >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(Math.round(n * 100) / 100);
}
export function prettyKey(k) {
  return String(k).replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\s+/g, ' ').trim()
    .replace(/^./, (c) => c.toUpperCase());
}
// guess a sensible display format for a table cell from its column name
export function fmtCell(key, v) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (typeof v !== 'number') return String(v);
  if (/prob|rate|share|util|discount|margin_pct|_pct$|pct$/i.test(key) && Math.abs(v) <= 1.5) return (v * 100).toFixed(1) + '%';
  if (/mrr|price|cost|revenue|profit|arr|benefit|saved|loss|impact|value|ar_?60|usd/i.test(key) && !/score|count|accounts|rank|horizon/i.test(key)) return fmtMoney(v, Math.abs(v) < 100 ? 2 : 0);
  return Number.isInteger(v) ? v.toLocaleString('en-US') : v.toLocaleString('en-US', { maximumFractionDigits: 2 });
}
export function timeAgo(iso) {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return 'unknown';
  const m = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (m < 2) return 'just now';
  if (m < 60) return m + ' minutes ago';
  if (m < 1440) return Math.round(m / 60) + ' hours ago';
  return Math.round(m / 1440) + ' days ago';
}
