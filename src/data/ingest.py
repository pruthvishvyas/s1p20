# [NOTE] src/data/ingest.py   | OUTCOME: UNDERSTAND (data health)
import glob, os
import numpy as np
import pandas as pd
from src.utils import write_json


def _find_raw(config):
    acct = config['COLS']['account']
    cands = [config['RAW_CSV']] + sorted(glob.glob(config['ROOT'] + 'data/raw/*.csv'))
    cands += sorted(glob.glob('data/raw/*.csv')) + sorted(glob.glob('*.csv'))
    for p in cands:
        if os.path.exists(p):
            try:
                if acct in pd.read_csv(p, nrows=2).columns:
                    return p
            except Exception:
                continue
    return None


def load_and_validate(config):
    c = config['COLS']
    path = _find_raw(config)
    if path is None:
        raise FileNotFoundError('No CSV containing column ' + c['account'] + ' found. Put it in ' + config['ROOT'] + 'data/raw/')
    df = pd.read_csv(path, keep_default_na=False, na_values=[''])
    print('[ingest] source:', path, '| shape:', df.shape)
    missing = [v for v in c.values() if v not in df.columns]
    if missing:
        raise ValueError('Schema check failed, missing columns: ' + str(missing))
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    print('[ingest] columns with nulls:', nulls.to_dict() if len(nulls) else 'none')
    month = pd.to_datetime(df[c['month']], errors='coerce')
    pnum = month.dt.year * 12 + month.dt.month
    d = pd.DataFrame({'a': df[c['account']], 'p': pnum}).sort_values(['a', 'p'])
    gaps = int((d.groupby('a')['p'].diff() > 1).sum())
    ident = (df[c['mrr_start']] + df[c['mrr_new']] + df[c['mrr_exp']] - df[c['mrr_con']] - df[c['mrr_churn']] - df[c['mrr_end']]).abs()
    churn_rows = df[df[c['churn']] == 1]
    n_months = int(month.nunique())
    v = {
        'source_file': path, 'rows': int(len(df)), 'cols': int(df.shape[1]), 'accounts': int(df[c['account']].nunique()),
        'months': n_months, 'first_month': str(month.min())[:10], 'last_month': str(month.max())[:10],
        'null_counts': {k: int(x) for k, x in nulls.items()},
        'null_month_rows': int(month.isnull().sum()),
        'duplicate_account_months': int(df.duplicated([c['account'], c['month']]).sum()),
        'account_month_gaps': gaps,
        'mrr_identity_mismatch_rows': int((ident > 0.01).sum()),
        'negative_value_rows': int((df[[c[k] for k in config['NONNEG_KEYS']]] < 0).any(axis=1).sum()),
        'churn_events': int(len(churn_rows)),
        'churn_rate_account_month': float(df[c['churn']].mean()),
        'churn_rows_with_positive_ending_mrr': int((churn_rows[c['mrr_end']] > 0).sum()),
        'churn_rows_missing_reason': int(churn_rows[c['churn_reason']].isnull().sum()),
        'target_balance': {str(k): int(x) for k, x in df[c['churn']].value_counts().items()},
        'categorical_levels': {k: sorted(df[c[k]].dropna().astype(str).unique().tolist())[:30] for k in config['CAT_KEYS']},
    }
    v['schema_ok'] = True
    v['quality_gates'] = {
        'min_rows_ok': v['rows'] >= config['MIN_ROWS'], 'min_accounts_ok': v['accounts'] >= config['MIN_ACCOUNTS'],
        'min_months_ok': n_months >= config['MIN_MONTHS'],
        'churn_model_ready': v['churn_events'] >= config['MIN_POS_TOTAL'],
        'forecast_ready': n_months >= config['MIN_MONTHS_FORECAST'],
    }
    for k, ok in v['quality_gates'].items():
        if not ok:
            print('[ingest] WARNING quality gate failed:', k, '- downstream phase will use a graceful fallback')
    write_json(v, config['VALIDATION_JSON'])
    print('[ingest] accounts:', v['accounts'], '| months:', n_months, '| churn events:', v['churn_events'],
          '| gaps:', gaps, '| duplicates:', v['duplicate_account_months'])
    return df
