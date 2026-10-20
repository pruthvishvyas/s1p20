import { useEffect, useState } from 'react';

const read = () => {
  const s = getComputedStyle(document.documentElement);
  const g = (n, d) => (s.getPropertyValue(n) || '').trim() || d;
  return {
    accent: g('--color-accent', '#4f46e5'), border: g('--color-border', '#e2e8f0'), text: g('--color-text-secondary', '#64748b'),
    surface: g('--color-surface', '#ffffff'), danger: g('--color-danger', '#e11d48'), warning: g('--color-warning', '#f59e0b'),
    success: g('--color-success', '#16a34a'), series: [1, 2, 3, 4, 5, 6].map((i) => g('--color-series-' + i, '#4f46e5'))
  };
};

// resolved theme colours (Recharts needs real values); recomputed whenever the theme toggles
export function useThemeColors() {
  const [c, setC] = useState(read);
  useEffect(() => {
    const obs = new MutationObserver(() => setC(read()));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => obs.disconnect();
  }, []);
  return c;
}
