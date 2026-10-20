import { useAlerts } from '../../hooks/monitor/useAlerts';
import { validateAlerts } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { SeverityBadge } from '../shared/SeverityBadge';

export function AlertCenter() {
  const { data: raw, loading, error } = useAlerts();
  if (loading) return <SkeletonCard height={150} count={2} />;
  const v = validateAlerts(raw);
  if (error || !v.valid) return <EmptyState message="No alert data available yet." action={RUN_HINT} />;
  if (!v.data.alerts.length) return <div className="card"><p>&#9989; No alerts. Every tracked goal is within its limit as of {v.data.as_of}.</p></div>;
  const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const list = [...v.data.alerts].sort((a, b) => (order[a.severity] ?? 3) - (order[b.severity] ?? 3));
  return (
    <div className="alert-list">
      {list.map((a, i) => (
        <div key={i} className={'card alert-item sev-border-' + String(a.severity).toLowerCase()}>
          <SeverityBadge severity={a.severity} /><span>{a.message}</span>
        </div>
      ))}
    </div>
  );
}
