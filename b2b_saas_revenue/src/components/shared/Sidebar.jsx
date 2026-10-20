import { NavLink } from 'react-router-dom';
import { CONTRACT } from '../../utils/contract';
import { outcomeInfo } from '../../utils/terminology';

const items = [
  { to: '/understand', label: 'UNDERSTAND', hint: outcomeInfo.understand.question, icon: '\u{1F50D}' },
  { to: '/decide', label: 'DECIDE', hint: outcomeInfo.decide.question, icon: '\u{1F9ED}' },
  { to: '/monitor', label: 'MONITOR', hint: outcomeInfo.monitor.question, icon: '\u{1F4E1}' },
  { to: '/explorer', label: 'Explorer', hint: 'Slice and drill into your data', icon: '\u{1F9E9}' },
  { to: '/manual', label: 'User Manual', hint: 'Plain-English guide', icon: '\u{1F4D6}' }
];
export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">{String(CONTRACT.project.name).charAt(0)}</span><span className="brand-name">{CONTRACT.project.name}</span></div>
      <nav>
        {items.map((it) => (
          <NavLink key={it.to} to={it.to} className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')} title={it.hint}>
            <span aria-hidden="true">{it.icon}</span>
            <span className="nav-text"><strong>{it.label}</strong><small>{it.hint}</small></span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
