import { useCallback, useState } from 'react';
import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useForecast = () => useData(dataPath('monitor', 'forecast'));

// calls the Worker (POST /api); if it is not reachable (e.g. npm run dev) falls back to the local forecast file
export function useForecastLookup(rows) {
  const [state, setState] = useState({ loading: false, result: null, error: null });
  const run = useCallback(async (value) => {
    const n = Number(value);
    if (value === '' || !Number.isFinite(n)) { setState({ loading: false, result: null, error: 'Enter the number of months ahead.' }); return; }
    setState({ loading: true, result: null, error: null });
    let note = null;
    try {
      const res = await fetch('/api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ input: n }) });
      const text = await res.text();
      let body = null;
      try { body = JSON.parse(text); } catch (e) { body = null; }
      if (res.ok && body && body.prediction !== undefined && body.prediction !== null) {
        setState({ loading: false, result: { ...body, source: 'live service' }, error: null });
        return;
      }
      throw new Error((body && body.error) || 'HTTP ' + res.status);
    } catch (e) {
      note = e.message;
    }
    const list = Array.isArray(rows) ? rows : [];
    if (list.length) {
      const r = list.reduce((a, b) => (Math.abs(b.horizon - n) < Math.abs(a.horizon - n) ? b : a));
      setState({ loading: false, result: { prediction: r.mrr_p50, range_low: r.mrr_p10, range_high: r.mrr_p90, input_received: n, nearest_key: r.horizon, source: 'local data file', note }, error: null });
    } else {
      setState({ loading: false, result: null, error: note || 'Forecast unavailable' });
    }
  }, [rows]);
  return { ...state, run };
}
