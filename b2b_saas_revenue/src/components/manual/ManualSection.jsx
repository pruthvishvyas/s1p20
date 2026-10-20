export function highlight(text, q) {
  if (!q) return text;
  const safe = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return String(text).split(new RegExp('(' + safe + ')', 'ig')).map((p, i) => (p.toLowerCase() === q.toLowerCase() ? <mark key={i}>{p}</mark> : p));
}
export function ManualSection({ title, items, q }) {
  return (
    <section className="manual-section card">
      <h2>{highlight(title, q)}</h2>
      {items.map((it, i) => (
        <div key={i} className="manual-item">
          <h4>{highlight(it.h, q)}</h4>
          {it.p.map((line, j) => <p key={j}>{highlight(line, q)}</p>)}
        </div>
      ))}
    </section>
  );
}
