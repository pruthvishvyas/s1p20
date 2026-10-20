import { useContext } from 'react';
import { ExplorerContext } from '../../context/ExplorerContext';
import { prettyKey } from '../../utils/formatters';

export function FilterBar({ dims, rows }) {
  const { filters, setFilter, clearFilters, activeFilters } = useContext(ExplorerContext);
  return (
    <div className="filter-bar">
      {dims.map((d) => {
        const opts = [...new Set(rows.map((r) => String(r[d])))].sort();
        return (
          <label key={d}>{prettyKey(d)}
            <select className="input" value={filters[d] ?? ''} onChange={(e) => setFilter(d, e.target.value === '' ? null : e.target.value)}>
              <option value="">All</option>
              {opts.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </label>
        );
      })}
      <button className="btn" onClick={clearFilters} disabled={!activeFilters}>Clear filters{activeFilters ? ' (' + activeFilters + ')' : ''}</button>
    </div>
  );
}
