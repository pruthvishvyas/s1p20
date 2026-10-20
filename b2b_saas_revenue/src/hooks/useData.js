import { useState, useEffect, useRef } from 'react';

function validateShape(data, path) {
  if (data === null || data === undefined) throw new Error('Empty response from ' + path);
  if (typeof data !== 'object') throw new Error('Expected object or array from ' + path + ', got ' + typeof data);
  return data;
}

// the ONLY place that fetches data. path === null means "the contract does not declare this file"
export function useData(path, options = {}) {
  const { transform, fallback = null } = options;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(path));
  const [error, setError] = useState(path ? null : 'Not declared in frontend_contract.json');
  const abortRef = useRef(null);

  useEffect(() => {
    if (!path) { setData(fallback); setLoading(false); setError('Not declared in frontend_contract.json'); return undefined; }
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    fetch(path, { signal: controller.signal, cache: 'no-cache' })
      .then(async (res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status + ' loading ' + path);
        const text = await res.text();
        if (!text || text.trim() === '') throw new Error('Empty file at ' + path);
        let parsed;
        try { parsed = JSON.parse(text); } catch (e) { throw new Error('Invalid JSON at ' + path); }
        const validated = validateShape(parsed, path);
        return transform ? transform(validated) : validated;
      })
      .then((result) => { if (!controller.signal.aborted) { setData(result); setLoading(false); } })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        console.error('useData error [' + path + ']:', err.message);
        setData(fallback); setError(err.message); setLoading(false);
      });
    return () => controller.abort();
  }, [path]);

  return { data, loading, error };
}
