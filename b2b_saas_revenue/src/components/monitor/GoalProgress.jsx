import { useGoalProgress } from '../../hooks/monitor/useGoalProgress';
import { useGoalOverrides } from '../../hooks/shared/useGoalOverrides';
import { goalKind } from '../../utils/goalStore';
import { validateGoalProgress } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';

const fmt = (g, v) => (v === null || v === undefined || !Number.isFinite(Number(v)) ? '\u2014' : g === 'mrr_target' ? '$' + Math.round(Number(v)).toLocaleString('en-US') : Number(v).toFixed(2));

export function GoalProgress() {
  const { data: raw, loading, error } = useGoalProgress();
  const overrides = useGoalOverrides();
  if (loading) return <SkeletonCard height={200} />;
  const v = validateGoalProgress(raw);
  if (error || !v.valid) return <EmptyState message="No goal progress available yet." action={RUN_HINT} />;
  return (
    <div className="goal-grid">
      {v.data.goals.map((g) => {
        const target = overrides[g.goal] !== undefined ? overrides[g.goal] : g.target;
        let status = 'not_set';
        if (target !== null && target !== undefined) {
          const breach = goalKind(g.goal) === 'max' ? g.actual > target : g.actual < target;
          status = breach ? 'breach' : 'on_track';
        }
        const label = { on_track: 'On track', breach: 'Off target', not_set: 'No target set' }[status];
        return (
          <div key={g.goal} className={'card goal-card goal-' + status}>
            <div className="kpi-label">{g.label}</div>
            <div className="kpi-value">{fmt(g.goal, g.actual)}</div>
            <div className="muted">Target: {fmt(g.goal, target)} {goalKind(g.goal) === 'max' ? '(stay below)' : '(stay above)'}</div>
            <span className={'badge status-' + status}>{label}</span>
          </div>
        );
      })}
    </div>
  );
}
