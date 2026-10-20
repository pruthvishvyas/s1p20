import { useAnomalies } from '../../hooks/understand/useAnomalies';
import { validateAnomalies } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { DataTable } from '../shared/DataTable';

export function AnomalyTable() {
  const { data: raw, loading, error } = useAnomalies();
  if (loading) return <SkeletonCard height={260} />;
  const { valid, data } = validateAnomalies(raw);
  if (error || !valid) return <EmptyState message="No anomaly data available yet." action={RUN_HINT} />;
  if (!data.items.length) return <EmptyState message="No unusual patterns were detected in this run." />;
  return (
    <div className="card">
      <p className="muted">{Number(data.total).toLocaleString('en-US')} unusual account-months flagged; the {data.items.length} most unusual are listed. The driver column shows what moved most (z = how many typical steps away from normal).</p>
      <DataTable rows={data.items} initialSort={{ key: 'anomaly_score', dir: 'desc' }} />
    </div>
  );
}
