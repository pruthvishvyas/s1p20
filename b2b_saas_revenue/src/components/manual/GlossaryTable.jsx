import { highlight } from './ManualSection';

export function GlossaryTable({ rows, q }) {
  return (
    <div className="table-wrap"><table className="table"><thead><tr><th>Term</th><th>What it means</th></tr></thead>
      <tbody>{rows.map(([t, d]) => <tr key={t}><td><strong>{highlight(t, q)}</strong></td><td className="wrap">{highlight(d, q)}</td></tr>)}</tbody></table></div>
  );
}
