import { useState, useMemo } from 'react';
import { useData } from '../../hooks/useData';
import { useSimulations } from '../../hooks/decide/useSimulations';
import { validateSimulation } from '../../utils/dataValidator';
import { fmtMoney, fmtPct, fmtInt } from '../../utils/formatters';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { useTerm } from '../shared/TerminologyProvider';

const nameOf = (p) => p.split('/').pop().replace('.json', '');
const TITLES = { price_change_impact: 'Change prices', retention_campaign_roi: 'Run a retention campaign', discount_policy_impact: 'Tighten discounts at renewal' };

function Stat({ label, value, tone }) {
  return <div className="card stat"><div className="kpi-label">{label}</div><div className={'kpi-value ' + (tone || '')}>{value}</div></div>;
}
const tone = (n) => (Number(n) > 0 ? 'up' : Number(n) < 0 ? 'down' : '');

function PriceSim({ d, R }) {
  const [i, setI] = useState(() => Math.max(0, d.scenarios.findIndex((s) => Number(s.price_change_pct) === 0)));
  const s = d.scenarios[Math.min(i, d.scenarios.length - 1)];
  return (
    <div>
      <label className="slider-label">Price change: <strong>{Number(s.price_change_pct) > 0 ? '+' : ''}{s.price_change_pct}%</strong></label>
      <input type="range" min="0" max={d.scenarios.length - 1} step="1" value={i} onChange={(e) => setI(Number(e.target.value))} className="slider" />
      <div className="stat-grid">
        <Stat label={'Expected next-month ' + R} value={fmtMoney(s.expected_next_month_mrr)} />
        <Stat label="Change vs today's plan" value={fmtMoney(s.delta_vs_baseline)} tone={tone(s.delta_vs_baseline)} />
        <Stat label="Per year" value={fmtMoney(s.delta_annualised)} tone={tone(s.delta_annualised)} />
        <Stat label="Expected lost accounts" value={Number(s.expected_churned_logos).toFixed(1)} />
      </div>
    </div>
  );
}
function CampaignSim({ d, R }) {
  const tops = useMemo(() => [...new Set(d.scenarios.map((s) => s.target_top_pct))].sort((a, b) => a - b), [d]);
  const saves = useMemo(() => [...new Set(d.scenarios.map((s) => s.save_rate))].sort((a, b) => a - b), [d]);
  const [t, setT] = useState(tops[Math.min(1, tops.length - 1)]);
  const [sv, setSv] = useState(saves[Math.min(1, saves.length - 1)]);
  const s = d.scenarios.find((x) => x.target_top_pct === t && x.save_rate === sv) || d.scenarios[0];
  return (
    <div>
      <div className="chips"><span className="muted">Contact the riskiest:</span>{tops.map((x) => <button key={x} className={'chip' + (x === t ? ' on' : '')} onClick={() => setT(x)}>{x}%</button>)}</div>
      <div className="chips"><span className="muted">Share of expected churn we prevent:</span>{saves.map((x) => <button key={x} className={'chip' + (x === sv ? ' on' : '')} onClick={() => setSv(x)}>{x}%</button>)}</div>
      <div className="stat-grid">
        <Stat label="Accounts contacted" value={fmtInt(s.accounts_targeted)} />
        <Stat label="Campaign cost" value={fmtMoney(s.campaign_cost)} />
        <Stat label="Gross profit protected" value={fmtMoney(s.protected_gross_profit)} />
        <Stat label="Net benefit" value={fmtMoney(s.net_benefit)} tone={tone(s.net_benefit)} />
        <Stat label="Return on spend" value={s.roi === null || s.roi === undefined ? '\u2014' : fmtPct(Number(s.roi) * 100, 0)} tone={tone(s.roi)} />
      </div>
      <p className="muted">Assumes a campaign cost of about {fmtMoney(d.cost_per_account)} per account. {d.assumption}</p>
    </div>
  );
}
function DiscountSim({ d, R }) {
  const [i, setI] = useState(Math.min(2, d.scenarios.length - 1));
  const s = d.scenarios[i];
  return (
    <div>
      <label className="slider-label">Reduce discounts by: <strong>{s.discount_reduction_pts} points</strong> for {fmtInt(s.eligible_accounts)} eligible accounts</label>
      <input type="range" min="0" max={d.scenarios.length - 1} step="1" value={i} onChange={(e) => setI(Number(e.target.value))} className="slider" />
      <div className="stat-grid">
        <Stat label={'Extra ' + R + ' if everyone stays'} value={fmtMoney(s.extra_mrr_if_all_stay)} tone={tone(s.extra_mrr_if_all_stay)} />
        <Stat label={'Expected net ' + R + ' change'} value={fmtMoney(s.expected_net_mrr_change)} tone={tone(s.expected_net_mrr_change)} />
        <Stat label="Per year" value={fmtMoney(s.expected_net_arr_change)} tone={tone(s.expected_net_arr_change)} />
      </div>
      <p className="muted">Eligible: {d.eligible_rule}. {d.assumption}</p>
    </div>
  );
}
const VIEWS = { price_change_impact: PriceSim, retention_campaign_roi: CampaignSim, discount_policy_impact: DiscountSim };

function SimCard({ path, R }) {
  const { data, loading, error } = useData(path);
  if (loading) return <SkeletonCard height={220} />;
  const v = validateSimulation(data);
  const key = nameOf(path);
  const View = VIEWS[key];
  return (
    <div className="card">
      <h3>{TITLES[key] || key.replace(/_/g, ' ')}</h3>
      {error || !v.valid || !View ? <EmptyState message="This scenario is not available yet." action={RUN_HINT} /> : <View d={v.data} R={R} />}
    </div>
  );
}

export function WhatIfSimulator() {
  const term = useTerm();
  const sims = useSimulations();
  if (!sims.length) return <EmptyState message="No what-if scenarios available yet." action={RUN_HINT} />;
  return <div className="sim-grid">{sims.map((s) => <ErrorBoundary key={s.path}><SimCard path={s.path} R={term('revenue')} /></ErrorBoundary>)}</div>;
}
