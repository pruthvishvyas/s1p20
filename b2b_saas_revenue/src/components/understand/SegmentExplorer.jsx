import { useState, useMemo } from 'react';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { useSegments } from '../../hooks/understand/useSegments';
import { validateSegments } from '../../utils/dataValidator';
import { useThemeColors } from '../../utils/colors';
import { useTerm } from '../shared/TerminologyProvider';
import { fmtMoney, fmtInt, fmtCompact } from '../../utils/formatters';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { DataTable } from '../shared/DataTable';
import { plural } from '../../utils/contract';

export function SegmentExplorer() {
  const term = useTerm();
  const c = useThemeColors();
  const { data: raw, loading, error } = useSegments();
  const [sel, setSel] = useState(null);
  const v = validateSegments(raw);
  const accounts = useMemo(() => (v.valid ? v.data.accounts.filter((a) => !sel || a.segment_name === sel) : []), [v.valid, raw, sel]);
  if (loading) return <SkeletonCard height={300} />;
  if (error || !v.valid) return <EmptyState message="No segment data available yet." action={RUN_HINT} />;
  const segs = v.data.segments;
  const R = term('revenue'), C = plural(term('customer'));
  return (
    <div>
      <div className="seg-grid">
        {segs.map((s) => (
          <button key={s.segment_name} className={'card seg-card' + (sel === s.segment_name ? ' selected' : '')} onClick={() => setSel(sel === s.segment_name ? null : s.segment_name)}>
            <strong>{s.segment_name}</strong>
            <span>{fmtInt(s.accounts)} {C.toLowerCase()}</span>
            <span>{fmtMoney(s.mrr)} {R}</span>
            <span className="muted">Health {Number(s.avg_health).toFixed(0)} &middot; seats used {(Number(s.avg_utilization) * 100).toFixed(0)}%</span>
          </button>
        ))}
      </div>
      <div className="card chart-card">
        <h3>{R} by segment</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={segs} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
            <XAxis dataKey="segment_name" tick={{ fill: c.text, fontSize: 12 }} interval={0} />
            <YAxis tick={{ fill: c.text, fontSize: 12 }} tickFormatter={fmtCompact} width={64} />
            <Tooltip contentStyle={{ background: c.surface, border: '1px solid ' + c.border, borderRadius: 8 }} formatter={(x) => [fmtMoney(x), R]} />
            <Bar dataKey="mrr" radius={[4, 4, 0, 0]} onClick={(d) => setSel(sel === d.segment_name ? null : d.segment_name)}>
              {segs.map((s, i) => <Cell key={i} fill={c.series[i % c.series.length]} fillOpacity={!sel || sel === s.segment_name ? 1 : 0.35} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="card">
        <h3>{sel ? sel : 'All segments'} &middot; {fmtInt(accounts.length)} {C.toLowerCase()} {sel && <button className="btn" onClick={() => setSel(null)}>Show all</button>}</h3>
        <DataTable rows={accounts} initialSort={{ key: 'Ending_MRR', dir: 'desc' }} />
      </div>
    </div>
  );
}
