// every validator returns { valid, data, error } - components render only when valid is true
const isObj = (x) => x !== null && typeof x === 'object' && !Array.isArray(x);

export function validateKPIs(raw) {
  if (!isObj(raw)) return { valid: false, data: null, error: 'KPIs must be an object' };
  return Number.isFinite(Number(raw.mrr)) ? { valid: true, data: raw, error: null } : { valid: false, data: null, error: 'KPI file has no MRR value' };
}
export function validateChartData(raw) {
  if (!isObj(raw) || !Array.isArray(raw.data)) return { valid: false, data: null, error: 'Invalid chart data' };
  const pts = raw.data.map((d) => ({ label: String(d?.label ?? ''), value: Number(d?.value) })).filter((d) => d.label !== '' && Number.isFinite(d.value));
  return pts.length ? { valid: true, data: { ...raw, data: pts }, error: null } : { valid: false, data: null, error: 'This chart has no data points yet.' };
}
export function validateInsights(raw) {
  if (!Array.isArray(raw)) return { valid: false, data: [], error: 'Insights must be an array' };
  const ok = raw.filter((i) => i && i.finding && i.severity);
  return { valid: ok.length > 0, data: ok, error: ok.length ? null : 'No valid insights' };
}
export function validateForecast(raw) {
  if (!isObj(raw) || !Array.isArray(raw.forecast) || raw.forecast.length === 0) return { valid: false, data: null, error: 'Invalid forecast data' };
  return { valid: true, data: raw, error: null };
}
export function validateAnomalies(raw) {
  const items = Array.isArray(raw) ? raw : isObj(raw) && Array.isArray(raw.items) ? raw.items : null;
  if (!items) return { valid: false, data: null, error: 'Invalid anomaly data' };
  return { valid: true, data: { total: isObj(raw) && raw.total_flagged != null ? raw.total_flagged : items.length, items }, error: null };
}
export function validateSegments(raw) {
  if (!isObj(raw) || !Array.isArray(raw.segments)) return { valid: false, data: null, error: 'Invalid segment data' };
  return { valid: raw.segments.length > 0, data: { segments: raw.segments, accounts: Array.isArray(raw.accounts) ? raw.accounts : [] }, error: raw.segments.length ? null : 'No segments' };
}
export function validateRecommendations(raw) {
  if (!isObj(raw) || !Array.isArray(raw.items)) return { valid: false, data: null, error: 'Invalid recommendation data' };
  return { valid: true, data: { items: raw.items, priority_counts: raw.priority_counts || {}, alert_counts: raw.alert_counts || {} }, error: null };
}
export function validateSimulation(raw) {
  if (!isObj(raw) || !Array.isArray(raw.scenarios) || raw.scenarios.length === 0) return { valid: false, data: null, error: 'Invalid simulation data' };
  return { valid: true, data: raw, error: null };
}
export function validateGoals(raw) {
  return isObj(raw) && Object.keys(raw).length ? { valid: true, data: raw, error: null } : { valid: false, data: null, error: 'No goals' };
}
export function validateGoalProgress(raw) {
  if (!isObj(raw) || !Array.isArray(raw.goals)) return { valid: false, data: null, error: 'Invalid goal progress' };
  return { valid: true, data: raw, error: null };
}
export function validateAlerts(raw) {
  if (!isObj(raw) || !Array.isArray(raw.alerts)) return { valid: false, data: null, error: 'Invalid alerts' };
  return { valid: true, data: raw, error: null };
}
