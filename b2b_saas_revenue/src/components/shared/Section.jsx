export function Section({ title, subtitle, children, right }) {
  return (
    <section className="section">
      <div className="section-head">
        <div><h2>{title}</h2>{subtitle && <p className="muted">{subtitle}</p>}</div>
        {right}
      </div>
      {children}
    </section>
  );
}
