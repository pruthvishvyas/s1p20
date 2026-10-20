import contract from '../contract.json';

export const CONTRACT = contract;
const clean = (p) => '/data/' + String(p).replace(/^\/+/, '');

// path of a single data file declared in outcomes.<group>.<key>; null when the contract does not declare it
export function dataPath(group, key) {
  const p = contract?.outcomes?.[group]?.[key];
  return p ? clean(p) : null;
}

// every file in contract.files whose name starts with prefix -> [{ path, outcome, purpose }]
export function filesUnder(prefix) {
  return (contract?.files || [])
    .filter((f) => f && typeof f.filename === 'string' && f.filename.startsWith(prefix))
    .map((f) => ({ path: clean(f.filename), outcome: f.outcome, purpose: f.purpose }));
}

export function metaPath(name) {
  const f = (contract?.files || []).find((x) => x?.filename?.endsWith('/' + name));
  return clean(f ? f.filename : 'meta/' + name);
}

export const term = (k) => contract?.terminology?.[k] ?? k;
export const plural = (s) => (s.endsWith('s') ? s : s + 's');
