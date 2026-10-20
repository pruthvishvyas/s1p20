import { useState } from 'react';
import { ResponsiveContainer, ComposedChart, Area, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { useForecast, useForecastLookup } from '../../hooks/monitor/useForecast';
import { validateForecast } from '../../utils/dataValidator';
import { useThemeColors } from '../../utils/colors';
import { useTerm } from '../shared/TerminologyProvider';
import { fmtMoney, fmtCompact, fmtPct } from '../../utils/formatters';
import { SkeletonCard } from '../shared/SkeletonCard';
import { EmptyState, RUN_HINT } from '../shared/EmptyState';
import { DataTable } from '../shared/DataTable';

export function Forecaster() {
  const term = useTerm();
  const c = useThemeColors();
  const { data: raw, loading, error } = useForecast();
  const v = validateForecast(raw);
  const rows = v.valid ? v.data.forecast : [];
  const lookup = useForecastLookup(rows);
  const [months, setMonths] = useState('3');
  if (loading) return <SkeletonCard height={380} />;
  if (error || !v.valid) return <EmptyState message="No forecast available yet." action={RUN_HINT} />;
  const R = term('revenue');
  const hist = (v.data.history || []).map((h) => ({ month: String(h.month).slice(0, 7), actual: Number(h.mrr) }));
  const fc = rows.map((r) => ({ month: String(r.month).slice(0, 7), forecast: Number(r.mrr_p50), band: [Number(r.mrr_p10), Number(r.mrr_p90)] }));
  const series = [...hist.map((h, i) => (i === hist.length - 1 && fc.length ? { ...h, forecast: h.actual } : h)), ...fc];
  const bt = v.data.backtest && v.data.method ? v.data.backtest[v.data.method] : null;
  const last = hist.length ? hist[hist.length - 1].actual : null;
  const end = fc.length ? fc[fc.length - 1].forecast : null;
  const r = lookup.result;
  return (
    <div>
      <div className="card chart-card">
        <h3>{R}: history and {rows.length}-month forecast</h3>
        <ResponsiveContainer width="100%" height={360}>
          <ComposedChart data={series} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
            <XAxis dataKey="month" tick={{ fill: c.text, fontSize: 12 }} interval="preserveStartEnd" minTickGap={28} />
            <YAxis tick={{ fill: c.text, fontSize: 12 }} tickFormatter={fmtCompact} width={64} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ background: c.surface, border: '1px solid ' + c.border, borderRadius: 8 }} formatter={(val) => (Array.isArray(val) ? fmtMoney(val[0]) + ' to ' + fmtMoney(val[1]) : fmtMoney(val))} />
            <Legend />
            <Area type="monotone" dataKey="band" name="Likely range (P10-P90)" stroke="none" fill={c.accent} fillOpacity={0.18} connectNulls />
            <Line type="monotone" dataKey="actual" name="Actual" stroke={c.text} strokeWidth={2} dot={false} connectNulls />
            <Line type="monotone" dataKey="forecast" name="Forecast (most likely)" stroke={c.accent} strokeWidth={2} strokeDasharray="6 4" dot={false} connectNulls />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="muted">
          {last !== null && end !== null ? R + ' today ' + fmtMoney(last) + ', expected ' + fmtMoney(end) + ' in ' + rows.length + ' months. ' : ''}
          {bt ? 'Past 3-month forecasts using this method were off by ' + fmtPct(bt.mape_3m * 100, 1) + ' on average. ' : ''}
          {v.data.low_confidence ? 'Warning: less than 12 months of history, treat this forecast with extra caution.' : ''}
        </p>
      </div>
      <div className="card">
        <h3>Look up a forecast</h3>
        <div className="lookup">
          <label>Months ahead <input className="input" type="number" min="1" value={months} onChange={(e) => setMonths(e.target.value)} /></label>
          <button className="btn primary" disabled={lookup.loading} onClick={() => lookup.run(months)}>{lookup.loading ? 'Looking up...' : 'Look up'}</button>
        </div>
        {lookup.error && <p className="error-text">{lookup.error}</p>}
        {r && (
          <p>Expected {R} in {r.nearest_key} month(s): <strong>{fmtMoney(r.prediction)}</strong>
            {r.range_low != null && r.range_high != null ? ' (likely between ' + fmtMoney(r.range_low) + ' and ' + fmtMoney(r.range_high) + ')' : ''}
            <span className="muted"> &middot; source: {r.source}{r.note ? ' (live service unavailable: ' + r.note + ')' : ''}</span></p>
        )}
      </div>
      <div className="card"><h3>Forecast table</h3><DataTable rows={rows} columns={['month', 'horizon', 'mrr_p10', 'mrr_p50', 'mrr_p90', 'new_mrr', 'expansion_mrr', 'contraction_mrr', 'churned_mrr']} /></div>
    </div>
  );
}
