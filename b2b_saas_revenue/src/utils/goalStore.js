// client-set goal targets live in the browser (localStorage), wrapped in try/catch; a custom event keeps tabs in sync
const KEY = 'goal_overrides';
export function getOverrides() {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { return {}; }
}
export function setOverride(goal, value) {
  const o = getOverrides();
  if (value === '' || value === null || value === undefined) delete o[goal]; else o[goal] = Number(value);
  try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) { /* storage unavailable */ }
  window.dispatchEvent(new Event('goals-changed'));
}
// 'max_' goals breach when actual is above target; 'min_' and mrr_target breach when below
export const goalKind = (key) => (String(key).startsWith('max_') ? 'max' : 'min');
