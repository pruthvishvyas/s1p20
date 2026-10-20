import { useKPIs } from '../../hooks/understand/useKPIs';
import { validateKPIs } from '../../utils/dataValidator';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { useTerm } from '../shared/TerminologyProvider';
import { plural } from '../../utils/contract';
import { fmtMoney, fmtPct, fmtInt } from '../../utils/formatters';

const FORMAT = { money: (v) => fmtMoney(v), pct: (v) => fmtPct(v), int: (v) => fmtInt(v), num: (v) => (Number.isFinite(Number(v)) ? Number(v).toFixed(1) : '\u2014') };

export function KPICards() {
  const term = useTerm();
  const { data: raw, loading, error } = useKPIs();
  if (loading) return <div className="kpi-grid"><SkeletonCard height={120} count={4} /></div>;
  const { valid, data: k } = validateKPIs(raw);
  if (!valid || error) return <EmptyState message={'No ' + term('revenue') + ' data available yet.'} action={RUN_HINT} />;
  const R = term('revenue'), C = plural(term('customer'));
  const cards = [
    { key: 'mrr', label: R, value: k.mrr, f: 'money', sub: 'Annualised: ' + fmtMoney(k.arr), trend: k.mrr_mom_pct, good: 'up' },
    { key: 'active', label: 'Active ' + C, value: k.active_accounts, f: 'int', sub: fmtInt(k.new_logos_last_month) + ' new, ' + fmtInt(k.churned_logos_last_month) + ' lost last month' },
    { key: 'nrr', label: 'Net revenue retention (month)', value: k.nrr_monthly_pct, f: 'pct', sub: k.nrr_trailing12_pct != null ? 'Trailing 12 months: ' + fmtPct(k.nrr_trailing12_pct) : 'Above 100% means the base grows by itself' },
    { key: 'grr', label: 'Gross revenue retention (month)', value: k.grr_monthly_pct, f: 'pct', sub: k.grr_trailing12_pct != null ? 'Trailing 12 months: ' + fmtPct(k.grr_trailing12_pct) : 'Share of ' + R + ' kept before upsell' },
    { key: 'logo', label: C + ' lost (month)', value: k.logo_churn_rate_pct, f: 'pct', sub: 'Logo churn rate', bad: true },
    { key: 'gm', label: 'Gross margin', value: k.gross_margin_pct, f: 'pct', sub: 'Contribution after acquisition cost: ' + fmtPct(k.contribution_margin_pct) },
    { key: 'ar', label: 'Overdue receivables (60+ days)', value: k.ar60_share_pct, f: 'pct', sub: fmtMoney(k.ar_60plus) + ' of ' + fmtMoney(k.ar_closing), bad: true },
    { key: 'health', label: 'Average health score', value: k.avg_health_score, f: 'num', sub: 'Out of 100' },
    { key: 'hr', label: 'High-risk ' + C, value: k.high_risk_accounts, f: 'int', sub: fmtPct(k.high_risk_mrr_share_pct) + ' of ' + R + ' sits here', bad: true },
    { key: 'risk', label: R + ' at risk next month', value: k.expected_mrr_at_risk, f: 'money', sub: 'Expected value from the churn model', bad: true }
  ].filter((c) => c.value !== null && c.value !== undefined);
  const dh = k.data_health || {};
  const gates = dh.quality_gates ? Object.entries(dh.quality_gates).filter(([, ok]) => ok === false).map(([n]) => n.replace(/_/g, ' ')) : [];
  return (
    <div>
      <div className="kpi-grid">
        {cards.map((c) => {
          const t = Number(c.trend);
          const showTrend = c.trend !== undefined && Number.isFinite(t);
          const positive = showTrend && (c.good === 'up' ? t >= 0 : t <= 0);
          return (
            <div key={c.key} className="card kpi-card">
              <div className="kpi-label">{c.label}</div>
              <div className="kpi-value">{FORMAT[c.f](c.value)}</div>
              {showTrend && <div className={'kpi-trend ' + (positive ? 'up' : 'down')}>{t >= 0 ? '\u2191' : '\u2193'} {Math.abs(t).toFixed(1)}% vs last month</div>}
              <div className="kpi-sub">{c.sub}</div>
            </div>
          );
        })}
      </div>
      <p className="muted data-health">
        Data as of {k.as_of}. {dh.rows ? fmtInt(dh.rows) + ' records, ' + fmtInt(dh.accounts) + ' ' + C.toLowerCase() + ', ' + dh.months + ' months (' + dh.first_month + ' to ' + dh.last_month + '). ' : ''}
        {gates.length ? 'Data checks needing attention: ' + gates.join(', ') + '.' : 'All data checks passed.'}
      </p>
    </div>
  );
}
