import { useMemo, useState } from 'react';
import { fmtCell, prettyKey } from '../../utils/formatters';

// generic sortable, paginated table. columns: optional array of keys (defaults to every key of the first row)
export function DataTable({ rows, columns, pageSize = 15, initialSort, wrapKeys = [] }) {
  const list = Array.isArray(rows) ? rows : [];
  const cols = useMemo(() => (columns && columns.length ? columns.filter((c) => list.some((r) => r && c in r)) : list[0] ? Object.keys(list[0]) : []), [columns, list]);
  const [sort, setSort] = useState(initialSort || null);
  const [page, setPage] = useState(0);
  const sorted = useMemo(() => {
    if (!sort || !cols.includes(sort.key)) return list;
    const dir = sort.dir === 'asc' ? 1 : -1;
    return [...list].sort((a, b) => {
      const x = a[sort.key], y = b[sort.key];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * dir;
    });
  }, [list, sort, cols]);
  const pages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const cur = Math.min(page, pages - 1);
  const view = sorted.slice(cur * pageSize, cur * pageSize + pageSize);
  if (!list.length || !cols.length) return <p className="muted">No rows to show.</p>;
  const click = (k) => { setPage(0); setSort((s) => (s && s.key === k ? { key: k, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: k, dir: 'desc' })); };
  return (
    <div>
      <div className="table-wrap">
        <table className="table">
          <thead><tr>{cols.map((c) => (
            <th key={c} onClick={() => click(c)} className="sortable">{prettyKey(c)}{sort && sort.key === c ? (sort.dir === 'asc' ? ' \u25B2' : ' \u25BC') : ''}</th>
          ))}</tr></thead>
          <tbody>{view.map((r, i) => (
            <tr key={i}>{cols.map((c) => <td key={c} className={wrapKeys.includes(c) ? 'wrap' : ''}>{fmtCell(c, r[c])}</td>)}</tr>
          ))}</tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="pager">
          <button className="btn" disabled={cur === 0} onClick={() => setPage(cur - 1)}>Previous</button>
          <span className="muted">Page {cur + 1} of {pages} &middot; {sorted.length.toLocaleString('en-US')} rows</span>
          <button className="btn" disabled={cur >= pages - 1} onClick={() => setPage(cur + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
