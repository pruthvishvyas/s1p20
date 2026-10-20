const cls = { HIGH: 'sev-high', MEDIUM: 'sev-medium', LOW: 'sev-low' };
const icon = { HIGH: '\u25CF', MEDIUM: '\u25CF', LOW: '\u25CF' };
export function SeverityBadge({ severity }) {
  const s = String(severity || 'LOW').toUpperCase();
  return <span className={'badge ' + (cls[s] || 'sev-low')}><span aria-hidden="true">{icon[s] || icon.LOW}</span> {s}</span>;
}
