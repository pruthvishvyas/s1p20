import { fmtCell, prettyKey } from '../../utils/formatters';
import { useTerm } from '../shared/TerminologyProvider';
import { plural } from '../../utils/contract';

export function DrillDownPanel({ drill, rows, metric, onClose }) {
  const term = useTerm();
  const open = Boolean(drill);
  const sub = open ? rows.filter((r) => String(r[drill.dim]) === drill.label) : [];
  const vals = sub.map((r) => Number(r[metric])).filter(Number.isFinite);
  const sum = vals.reduce((a, b) => a + b, 0);
  const idKey = sub[0] ? Object.keys(sub[0]).find((k) => /id$/i.test(k)) : null;
  const top = [...sub].sort((a, b) => Number(b[metric]) - Number(a[metric])).slice(0, 5);
  return (
    <aside className={'drill' + (open ? ' open' : '')} aria-hidden={!open}>
      {open && (
        <div>
          <div className="drill-head"><h3>{prettyKey(drill.dim)}: {drill.label}</h3><button className="btn" onClick={onClose}>Close &times;</button></div>
          <p>{plural(term('customer'))}: <strong>{sub.length.toLocaleString('en-US')}</strong></p>
          <p>Total {prettyKey(metric)}: <strong>{fmtCell(metric, sum)}</strong></p>
          <p>Average {prettyKey(metric)}: <strong>{fmtCell(metric, vals.length ? sum / vals.length : null)}</strong></p>
          <h4>Top 5 by {prettyKey(metric)}</h4>
          <ol>{top.map((r, i) => <li key={i}>{idKey ? r[idKey] : 'Row ' + (i + 1)} &mdash; {fmtCell(metric, r[metric])}</li>)}</ol>
        </div>
      )}
    </aside>
  );
}
