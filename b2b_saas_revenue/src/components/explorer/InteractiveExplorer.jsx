import { useContext, useEffect, useMemo, useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { ExplorerProvider } from '../../context/ExplorerContext';
import { ExplorerContext } from '../../context/ExplorerContext';
import { useData } from '../../hooks/useData';
import { dataPath } from '../../utils/contract';
import { useThemeColors } from '../../utils/colors';
import { fmtCell, fmtCompact, prettyKey } from '../../utils/formatters';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { DataTable } from '../shared/DataTable';
import { FilterBar } from './FilterBar';
import { DrillDownPanel } from './DrillDownPanel';

// detect which columns can be sliced (dimensions) and which can be measured (metrics)
function profile(rows) {
  if (!rows.length) return { dims: [], metrics: [] };
  const keys = Object.keys(rows[0]);
  const dims = [], metrics = [];
  keys.forEach((k) => {
    const vals = rows.map((r) => r[k]).filter((v) => v !== null && v !== undefined && v !== '');
    if (!vals.length) return;
    if (vals.every((v) => typeof v === 'number')) { metrics.push(k); return; }
    const distinct = new Set(vals.map(String)).size;
    if (distinct >= 2 && distinct <= 25 && distinct < rows.length * 0.6 && !/id$/i.test(k)) dims.push(k);
  });
  return { dims, metrics };
}
function aggregate(rows, dim, metric, agg) {
  const m = new Map();
  rows.forEach((r) => {
    const k = String(r[dim]);
    const o = m.get(k) || { label: k, count: 0, sum: 0, n: 0 };
    o.count += 1;
    const v = Number(r[metric]);
    if (Number.isFinite(v)) { o.sum += v; o.n += 1; }
    m.set(k, o);
  });
  return [...m.values()].map((o) => ({ label: o.label, count: o.count, value: agg === 'count' ? o.count : agg === 'avg' ? (o.n ? o.sum / o.n : 0) : o.sum })).sort((a, b) => b.value - a.value);
}

function Inner() {
  const seg = useData(dataPath('understand', 'segments'));
  const rec = useData(dataPath('decide', 'recommendations'));
  const colors = useThemeColors();
  const { filters, setFilter, clearFilters } = useContext(ExplorerContext);
  const [ds, setDs] = useState('segments');
  const [metric, setMetric] = useState('');
  const [agg, setAgg] = useState('sum');
  const [dim, setDim] = useState('');
  const [drill, setDrill] = useState(null);
  const [copied, setCopied] = useState('');
  const rows = useMemo(() => (ds === 'segments' ? (Array.isArray(seg.data?.accounts) ? seg.data.accounts : []) : (Array.isArray(rec.data?.items) ? rec.data.items : [])), [ds, seg.data, rec.data]);
  const { dims, metrics } = useMemo(() => profile(rows), [rows]);
  useEffect(() => {
    setDrill(null); clearFilters();
    setMetric((m) => (metrics.includes(m) ? m : metrics.find((x) => /mrr/i.test(x)) || metrics[0] || ''));
    setDim((d) => (dims.includes(d) ? d : dims[0] || ''));
  }, [ds, dims.join('|'), metrics.join('|')]);
  const loading = ds === 'segments' ? seg.loading : rec.loading;
  if (loading) return <SkeletonCard height={400} />;
  if (!rows.length || !dims.length || !metrics.length) return <EmptyState message="No data available to explore yet." action={RUN_HINT} />;
  const matches = (r, skip) => Object.entries(filters).every(([k, v]) => k === skip || String(r[k]) === v);
  const filtered = rows.filter((r) => matches(r));
  const vals = filtered.map((r) => Number(r[metric])).filter(Number.isFinite);
  const total = vals.reduce((a, b) => a + b, 0);
  const others = dims.filter((d) => d !== dim).slice(0, 2);
  const pick = (d, label) => { setFilter(d, label); setDrill(filters[d] === label ? null : { dim: d, label }); };
  const barChart = (d, h) => {
    const data = aggregate(rows.filter((r) => matches(r, d)), d, metric, agg);
    return (
      <ResponsiveContainer width="100%" height={h}>
        <BarChart data={data} margin={{ top: 10, right: 16, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
          <XAxis dataKey="label" tick={{ fill: colors.text, fontSize: 11 }} interval={0} />
          <YAxis tick={{ fill: colors.text, fontSize: 12 }} tickFormatter={fmtCompact} width={60} />
          <Tooltip contentStyle={{ background: colors.surface, border: '1px solid ' + colors.border, borderRadius: 8 }} formatter={(v, n, p) => [fmtCell(agg === 'count' ? 'count' : metric, v), agg + ' of ' + prettyKey(metric) + ' (' + p.payload.count + ' rows)']} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]} cursor="pointer" onClick={(e) => e && pick(d, e.label)}>
            {data.map((x, i) => <Cell key={i} fill={colors.accent} fillOpacity={filters[d] && filters[d] !== x.label ? 0.3 : 1} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  };
  const copy = async () => {
    const txt = 'Explorer view | dataset: ' + ds + ' | rows: ' + filtered.length + ' of ' + rows.length + ' | ' + agg + ' of ' + prettyKey(metric) + ': ' + fmtCell(metric, total) + ' | filters: ' + (Object.entries(filters).map(([k, v]) => prettyKey(k) + '=' + v).join(', ') || 'none');
    try { await navigator.clipboard.writeText(txt); setCopied('Copied to clipboard'); } catch (e) { setCopied('Copy not available in this browser'); }
    setTimeout(() => setCopied(''), 2500);
  };
  return (
    <div className="explorer">
      <div className="card explorer-controls">
        <label>Data <select className="input" value={ds} onChange={(e) => setDs(e.target.value)}><option value="segments">All active accounts</option><option value="actions">Accounts needing action</option></select></label>
        <label>Measure <select className="input" value={metric} onChange={(e) => setMetric(e.target.value)}>{metrics.map((m) => <option key={m} value={m}>{prettyKey(m)}</option>)}</select></label>
        <label>Calculation <select className="input" value={agg} onChange={(e) => setAgg(e.target.value)}><option value="sum">Total</option><option value="avg">Average</option><option value="count">Count</option></select></label>
        <label>Group by <select className="input" value={dim} onChange={(e) => setDim(e.target.value)}>{dims.map((d) => <option key={d} value={d}>{prettyKey(d)}</option>)}</select></label>
        <button className="btn" onClick={copy}>Copy summary</button>{copied && <span className="muted">{copied}</span>}
      </div>
      <div className="sticky-filters card"><FilterBar dims={dims} rows={rows} /></div>
      <div className="kpi-grid">
        <div className="card kpi-card"><div className="kpi-label">Rows in view</div><div className="kpi-value">{filtered.length.toLocaleString('en-US')}</div><div className="kpi-sub">of {rows.length.toLocaleString('en-US')}</div></div>
        <div className="card kpi-card"><div className="kpi-label">Total {prettyKey(metric)}</div><div className="kpi-value">{fmtCell(metric, total)}</div></div>
        <div className="card kpi-card"><div className="kpi-label">Average {prettyKey(metric)}</div><div className="kpi-value">{fmtCell(metric, vals.length ? total / vals.length : null)}</div></div>
      </div>
      <div className="card chart-card"><h3>{agg === 'count' ? 'Count' : (agg === 'avg' ? 'Average ' : 'Total ') + prettyKey(metric)} by {prettyKey(dim)} <span className="muted">(click a bar to filter everything)</span></h3>{barChart(dim, 340)}</div>
      <div className="chart-grid">
        {others.map((d) => <div key={d} className="card chart-card"><h3>By {prettyKey(d)}</h3>{barChart(d, 260)}</div>)}
      </div>
      <div className="card"><h3>Detail rows</h3><DataTable rows={filtered} pageSize={12} /></div>
      <DrillDownPanel drill={drill} rows={rows} metric={metric} onClose={() => setDrill(null)} />
    </div>
  );
}

export function InteractiveExplorer() {
  return <ErrorBoundary><ExplorerProvider><Inner /></ExplorerProvider></ErrorBoundary>;
}
