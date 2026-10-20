import { ThemeToggle } from './ThemeToggle';
import { useRunLog } from '../../hooks/shared/useRunLog';
import { timeAgo } from '../../utils/formatters';
import { CONTRACT } from '../../utils/contract';

export function Header({ title }) {
  const { last } = useRunLog();
  return (
    <header className="header">
      <div><h1>{title}</h1><p className="muted">{CONTRACT.project.description}</p></div>
      <div className="header-right">
        <span className="muted" title={last ? last.timestamp : ''}>Last updated: {last ? timeAgo(last.timestamp) : 'unknown'}</span>
        <ThemeToggle />
      </div>
    </header>
  );
}
