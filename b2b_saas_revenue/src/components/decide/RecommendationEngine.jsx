import { useState, useMemo } from 'react';
import { useRecommendations } from '../../hooks/decide/useRecommendations';
import { validateRecommendations } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { DataTable } from '../shared/DataTable';
import { prettyKey } from '../../utils/formatters';

const PREFERRED = ['Account_ID', 'priority', 'alerts', 'recommendations', 'mrr_at_risk', 'churn_prob', 'risk_level', 'Ending_MRR', 'months_to_renewal', 'Health_Score', 'seat_utilization'];

export function RecommendationEngine() {
  const { data: raw, loading, error } = useRecommendations();
  const [pri, setPri] = useState('ALL');
  const [alert, setAlert] = useState('ALL');
  const v = validateRecommendations(raw);
  const rows = useMemo(() => (v.valid ? v.data.items.filter((r) => (pri === 'ALL' || r.priority === pri) && (alert === 'ALL' || String(r.alerts || '').split('|').includes(alert))) : []), [v.valid, raw, pri, alert]);
  if (loading) return <SkeletonCard height={300} />;
  if (error || !v.valid) return <EmptyState message="No recommendations available yet." action={RUN_HINT} />;
  const pc = v.data.priority_counts, ac = v.data.alert_counts;
  return (
    <div className="card">
      <p className="muted">Each row is an account that needs attention, ranked by urgency. P1 = act this week, P2 = this month, P3 = plan for it.</p>
      <div className="chips">
        <button className={'chip' + (pri === 'ALL' ? ' on' : '')} onClick={() => setPri('ALL')}>All priorities</button>
        {Object.keys(pc).sort().map((p) => <button key={p} className={'chip' + (pri === p ? ' on' : '')} onClick={() => setPri(p)}>{p.replace('_', ' ')} ({pc[p]})</button>)}
      </div>
      <div className="chips">
        <button className={'chip' + (alert === 'ALL' ? ' on' : '')} onClick={() => setAlert('ALL')}>Any reason</button>
        {Object.keys(ac).sort((a, b) => ac[b] - ac[a]).map((a) => <button key={a} className={'chip' + (alert === a ? ' on' : '')} onClick={() => setAlert(a)}>{prettyKey(a)} ({ac[a]})</button>)}
      </div>
      {rows.length ? <DataTable rows={rows} columns={PREFERRED} wrapKeys={['alerts', 'recommendations']} pageSize={12} /> : <EmptyState message="No accounts match these filters." />}
    </div>
  );
}
