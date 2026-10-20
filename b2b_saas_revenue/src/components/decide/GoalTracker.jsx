import { useState } from 'react';
import { useGoals } from '../../hooks/decide/useGoals';
import { useGoalOverrides } from '../../hooks/shared/useGoalOverrides';
import { setOverride } from '../../utils/goalStore';
import { validateGoals } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { prettyKey } from '../../utils/formatters';

function GoalRow({ id, g, override }) {
  const base = g.value;
  const shown = override !== undefined ? override : base;
  const [draft, setDraft] = useState(shown === null || shown === undefined ? '' : String(shown));
  const editable = typeof base === 'number' || base === null;
  return (
    <div className="goal-row">
      <div><strong>{prettyKey(id)}</strong><p className="muted">{g.description || ''}</p></div>
      <div className="goal-input">
        {editable ? (
          <>
            <input className="input" type="number" value={draft} placeholder="Set target" onChange={(e) => setDraft(e.target.value)} onBlur={() => setOverride(id, draft)} />
            <span className="muted">{g.unit}</span>
            {override !== undefined && <button className="btn" onClick={() => { setOverride(id, ''); setDraft(base === null ? '' : String(base)); }}>Reset</button>}
          </>
        ) : <span>{String(base)} <span className="muted">{g.unit}</span></span>}
      </div>
    </div>
  );
}

export function GoalTracker() {
  const { data: raw, loading, error } = useGoals();
  const overrides = useGoalOverrides();
  if (loading) return <SkeletonCard height={200} />;
  const { valid, data } = validateGoals(raw);
  if (error || !valid) return <EmptyState message="No goals available yet." action={RUN_HINT} />;
  return (
    <div className="card">
      <p className="muted">Targets are saved in this browser. Edit a number and click away to apply it; the Goal Progress panel updates immediately.</p>
      {Object.entries(data).map(([id, g]) => <GoalRow key={id} id={id} g={g || {}} override={overrides[id]} />)}
    </div>
  );
}
