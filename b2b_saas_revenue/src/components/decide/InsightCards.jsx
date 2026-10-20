import { useState } from 'react';
import { useInsights } from '../../hooks/decide/useInsights';
import { validateInsights } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { SeverityBadge } from '../shared/SeverityBadge';
import { fmtMoney } from '../../utils/formatters';

export function InsightCards() {
  const { data: raw, loading, error } = useInsights();
  const [f, setF] = useState('ALL');
  if (loading) return <SkeletonCard height={150} count={3} />;
  const { valid, data } = validateInsights(raw);
  if (error || !valid) return <EmptyState message="No insights available yet." action={RUN_HINT} />;
  const list = [...data].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99)).filter((i) => f === 'ALL' || i.severity === f);
  return (
    <div>
      <div className="chips">
        {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((s) => <button key={s} className={'chip' + (f === s ? ' on' : '')} onClick={() => setF(s)}>{s === 'ALL' ? 'All insights' : s}</button>)}
      </div>
      <div className="insight-grid">
        {list.map((i, n) => (
          <article key={n} className={'card insight sev-border-' + String(i.severity).toLowerCase()}>
            <div className="insight-head"><SeverityBadge severity={i.severity} /><span className="muted">{i.category}</span></div>
            <p className="insight-finding">{i.finding}</p>
            <p className="muted"><strong>Evidence:</strong> {i.evidence}</p>
            <p className="insight-action"><strong>Do this week:</strong> {i.action}</p>
            {Number(i.impact_usd_monthly) > 0 && <p className="muted">Monthly value at stake: {fmtMoney(i.impact_usd_monthly)}</p>}
          </article>
        ))}
        {!list.length && <EmptyState message="No insights at this severity level." />}
      </div>
    </div>
  );
}
