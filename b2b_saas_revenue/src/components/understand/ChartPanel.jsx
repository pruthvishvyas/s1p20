import { ResponsiveContainer, LineChart, Line, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { useData } from '../../hooks/useData';
import { useCharts } from '../../hooks/understand/useCharts';
import { validateChartData } from '../../utils/dataValidator';
import { useThemeColors } from '../../utils/colors';
import { fmtCompact, fmtMoney, fmtPct } from '../../utils/formatters';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { ErrorBoundary } from '../shared/ErrorBoundary';

function tipFmt(spec) {
  const y = String(spec.y_label || '');
  if (y.includes('$')) return (v) => fmtMoney(v);
  if (y.includes('%')) return (v) => fmtPct(v, 2);
  return (v) => fmtCompact(v);
}

function renderChart(spec, c) {
  const rows = spec.data;
  const horizontal = spec.type === 'bar' && (rows.length > 8 || Math.max(...rows.map((r) => r.label.length)) > 12);
  const axis = { fill: c.text, fontSize: 12 };
  const tip = { contentStyle: { background: c.surface, border: '1px solid ' + c.border, borderRadius: 8 }, formatter: (v) => [tipFmt(spec)(v), spec.y_label || 'Value'] };
  if (spec.type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
          <XAxis dataKey="label" tick={axis} interval="preserveStartEnd" minTickGap={28} />
          <YAxis tick={axis} tickFormatter={fmtCompact} width={64} />
          <Tooltip {...tip} />
          <Line type="monotone" dataKey="value" stroke={c.accent} strokeWidth={2} dot={rows.length < 14} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  if (horizontal) {
    const h = Math.max(320, rows.length * 34 + 60);
    return (
      <ResponsiveContainer width="100%" height={h}>
        <BarChart data={rows} layout="vertical" margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
          <XAxis type="number" tick={axis} tickFormatter={fmtCompact} />
          <YAxis type="category" dataKey="label" tick={{ ...axis, fontSize: 11 }} width={150} interval={0} />
          <Tooltip {...tip} />
          <Bar dataKey="value" fill={c.accent} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={rows} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
        <XAxis dataKey="label" tick={axis} interval="preserveStartEnd" minTickGap={20} />
        <YAxis tick={axis} tickFormatter={fmtCompact} width={64} />
        <Tooltip {...tip} />
        <Bar dataKey="value" fill={c.accent} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ChartCard({ path }) {
  const { data, loading, error } = useData(path);
  const colors = useThemeColors();
  if (loading) return <SkeletonCard height={380} />;
  const v = validateChartData(data);
  return (
    <div className="card chart-card">
      <h3>{data?.title || 'Chart'}</h3>
      {error || !v.valid ? <EmptyState message={error ? 'This chart could not be loaded.' : v.error} action={error ? RUN_HINT : null} /> : renderChart(v.data, colors)}
    </div>
  );
}

// outcome: 'UNDERSTAND' | 'DECIDE' | 'MONITOR' - shows the charts the pipeline tagged for that outcome
export function ChartPanel({ outcome }) {
  const charts = useCharts(outcome);
  if (!charts.length) return <EmptyState message="No charts available yet." action={RUN_HINT} />;
  return (
    <div className="chart-grid">
      {charts.map((c) => <ErrorBoundary key={c.path}><ChartCard path={c.path} /></ErrorBoundary>)}
    </div>
  );
}
