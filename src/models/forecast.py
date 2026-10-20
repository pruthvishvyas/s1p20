# [NOTE] src/models/forecast.py   | OUTCOME: MONITOR (6-month MRR forecast with honest uncertainty band)
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from src.utils import monthly_summary, save_fig


def _driver_path(mrr_last, rates, H):
    path, comp, mrr = [], [], mrr_last
    for _ in range(H):
        new, ex, co, ch = rates['new'], mrr * rates['exp'], mrr * rates['con'], mrr * rates['churn']
        mrr = mrr + new + ex - co - ch
        path.append(mrr); comp.append((new, ex, co, ch))
    return path, comp


def _window_rates(ms, end, W):
    w = ms.iloc[max(0, end - W + 1):end + 1]
    st = w['mrr_start'].replace(0, np.nan)
    f = lambda col: float((w[col] / st).replace([np.inf, -np.inf], np.nan).mean())
    return {'new': float(w['mrr_new'].mean()), 'exp': f('mrr_exp'), 'con': f('mrr_con'), 'churn': f('mrr_churn'),
            'drift': float(w['net_new_mrr'].mean())}


def _predict(ms, end, h, W, method):
    last = float(ms['mrr_end'].iloc[end])
    if method == 'naive':
        return last
    r = _window_rates(ms, end, W)
    if method == 'drift':
        return last + h * r['drift']
    return _driver_path(last, r, h)[0][-1]


def run_forecast(df, config):
    c = config['COLS']
    ms = monthly_summary(df, c)
    n, H, W = len(ms), config['FORECAST_HORIZON_MONTHS'], min(config['FORECAST_WINDOW'], max(2, len(ms) - 1))
    ready = n >= config['MIN_MONTHS_FORECAST']
    if n < 4:
        raise ValueError('Need at least 4 months of history to forecast, found ' + str(n))
    origins = list(range(W, n - 3))[-9:]
    bt = {}
    for method in ['naive', 'drift', 'driver']:
        errs = [(_predict(ms, o, 3, W, method) - float(ms['mrr_end'].iloc[o + 3])) for o in origins]
        act = [float(ms['mrr_end'].iloc[o + 3]) for o in origins]
        if errs:
            bt[method] = {'mape_3m': float(np.mean([abs(e) / max(a, 1) for e, a in zip(errs, act)])), 'err_sd': float(np.std(errs)), 'points': len(errs)}
    best = min(bt, key=lambda k: bt[k]['mape_3m']) if bt else 'drift'
    sd3 = bt[best]['err_sd'] if bt else 0.05 * float(ms['mrr_end'].iloc[-1])
    if not bt:
        print('[forecast] WARNING: too little history for a backtest; using drift with a 5% heuristic band')
    if not ready:
        print('[forecast] WARNING: <', config['MIN_MONTHS_FORECAST'], 'months of history -> forecast flagged low_confidence')
    last = float(ms['mrr_end'].iloc[-1])
    rates = _window_rates(ms, n - 1, W)
    months = pd.date_range(ms['month'].iloc[-1] + pd.offsets.MonthBegin(1), periods=H, freq='MS')
    rows = []
    path, comp = _driver_path(last, rates, H)
    for i in range(H):
        h = i + 1
        centre = last if best == 'naive' else (last + h * rates['drift'] if best == 'drift' else path[i])
        band = 1.2816 * sd3 * np.sqrt(h / 3.0)
        rows.append({'month': months[i], 'horizon': h, 'mrr_p10': max(centre - band, 0), 'mrr_p50': centre, 'mrr_p90': centre + band,
                     'new_mrr': comp[i][0] if best == 'driver' else np.nan, 'expansion_mrr': comp[i][1] if best == 'driver' else np.nan,
                     'contraction_mrr': comp[i][2] if best == 'driver' else np.nan, 'churned_mrr': comp[i][3] if best == 'driver' else np.nan})
    fc = pd.DataFrame(rows)
    fc.to_csv(config['FORECAST_CSV'], index=False, encoding='utf-8')
    joblib.dump({'method': best, 'window': W, 'rates': rates, 'last_mrr': last, 'last_month': str(ms['month'].iloc[-1])[:10],
                 'backtest': bt, 'err_sd_3m': sd3, 'low_confidence': (not ready)}, config['FORECAST_MODEL'])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    hist = ms.tail(24)
    ax.plot(hist['month'], hist['mrr_end'], color='#264653', lw=2, label='Actual MRR')
    ax.plot(fc['month'], fc['mrr_p50'], color='#e76f51', lw=2, label='Forecast (' + best + ')')
    ax.fill_between(fc['month'], fc['mrr_p10'], fc['mrr_p90'], color='#e76f51', alpha=0.2, label='P10-P90')
    ax.legend(); ax.set_title('Q [MONITOR] Where will MRR be over the next ' + str(H) + ' months?')
    save_fig(fig, config['REPORTS_DIR'] + 'forecast_mrr.png')
    res = {'method': best, 'backtest': bt, 'mape_3m': bt.get(best, {}).get('mape_3m'), 'end_mrr_p50': float(fc['mrr_p50'].iloc[-1]), 'last_mrr': last}
    if bt.get(best):
        print('[forecast] best method: %s | 3-month backtest MAPE %.2f%% (naive %.2f%%)' % (best, 100 * bt[best]['mape_3m'], 100 * bt.get('naive', bt[best])['mape_3m']))
    print('[forecast] MRR now %.0f -> %d months ahead (P50) %.0f' % (last, H, res['end_mrr_p50']))
    return res
