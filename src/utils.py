# [NOTE] src/utils.py   | shared helpers
import json, os, sys
import matplotlib
if 'ipykernel' not in sys.modules:
    matplotlib.use('Agg')
import numpy as np
import pandas as pd


def safe_div(a, b, fill=0.0):
    a = a if isinstance(a, pd.Series) else pd.Series(a)
    b = b if isinstance(b, pd.Series) else pd.Series(b, index=a.index)
    out = a / b.replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan).fillna(fill)


def _clean(o):
    if o is pd.NaT:
        return None
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 4)
    if isinstance(o, (pd.Timestamp, pd.Period)):
        return str(o)[:10]
    return o


def write_json(obj, path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    text = json.dumps(_clean(obj), indent=2, ensure_ascii=False).replace(chr(0xfffd), '-')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv(path, date_cols=()):
    df = pd.read_csv(path, keep_default_na=False, na_values=[''])
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def save_fig(fig, path):
    import matplotlib.pyplot as plt
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches='tight')
    if 'ipykernel' in sys.modules:
        plt.show()
    plt.close(fig)


def monthly_summary(df, c):
    d = df.copy()
    d['_s'] = (d[c['mrr_start']] > 0).astype(int)
    d['_e'] = (d[c['mrr_end']] > 0).astype(int)
    agg = {'mrr_start': (c['mrr_start'], 'sum'), 'mrr_new': (c['mrr_new'], 'sum'), 'mrr_exp': (c['mrr_exp'], 'sum'),
           'mrr_con': (c['mrr_con'], 'sum'), 'mrr_churn': (c['mrr_churn'], 'sum'), 'mrr_end': (c['mrr_end'], 'sum'),
           'revenue': (c['revenue'], 'sum'), 'gross_profit': (c['gross_profit'], 'sum'),
           'contribution': (c['contrib'], 'sum'), 'cac': (c['cac'], 'sum'), 'invoiced': (c['invoiced'], 'sum'),
           'cash': (c['cash'], 'sum'), 'ar_close': (c['ar_close'], 'sum'), 'ar60': (c['ar60'], 'sum'),
           'bad_debt': (c['bad_debt'], 'sum'), 'churned_logos': (c['churn'], 'sum'),
           'new_logos': (c['new_logo'], 'sum'), 'accounts_start': ('_s', 'sum'), 'accounts_end': ('_e', 'sum')}
    out = d.groupby(c['month']).agg(**agg).reset_index().rename(columns={c['month']: 'month'})
    out = out.sort_values('month').reset_index(drop=True)
    out['net_new_mrr'] = out['mrr_end'] - out['mrr_start']
    out['logo_churn_rate'] = safe_div(out['churned_logos'], out['accounts_start'])
    out['gross_revenue_churn'] = safe_div(out['mrr_con'] + out['mrr_churn'], out['mrr_start'])
    out['grr'] = 1 - out['gross_revenue_churn']
    out['nrr'] = safe_div(out['mrr_start'] + out['mrr_exp'] - out['mrr_con'] - out['mrr_churn'], out['mrr_start'])
    out['gross_margin_pct'] = safe_div(out['gross_profit'], out['revenue'])
    out['contribution_margin_pct'] = safe_div(out['contribution'], out['revenue'])
    out['ar60_share'] = safe_div(out['ar60'], out['ar_close'])
    return out
