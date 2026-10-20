# [NOTE] src/data/clean.py   | OUTCOME: UNDERSTAND
import numpy as np
import pandas as pd


def clean(df, config):
    c = config['COLS']
    df = df.copy()
    n0 = len(df)
    df[c['month']] = pd.to_datetime(df[c['month']], errors='coerce').dt.to_period('M').dt.to_timestamp()
    df[c['cohort']] = pd.to_datetime(df[c['cohort']], errors='coerce').dt.to_period('M').dt.to_timestamp()
    df = df.dropna(subset=[c['month'], c['account']])
    num_keys = [k for k in c if k not in config['CAT_KEYS'] + ['month', 'account', 'cohort', 'churn_reason']]
    for k in num_keys:
        df[c[k]] = pd.to_numeric(df[c[k]], errors='coerce')
    for k in config['CAT_KEYS']:
        df[c[k]] = df[c[k]].astype(str).str.strip().replace({'nan': 'Unknown', '': 'Unknown', 'None': 'Unknown'})
    if df[c['discount']].max() > 1.5:
        df[c['discount']] = df[c['discount']] / 100.0
        print('[clean] Discount_Pct looked like 0-100, rescaled to 0-1')
    df[c['discount']] = df[c['discount']].clip(0, 1)
    # nulls: money flows -> 0 ; behavioural metrics -> carry forward inside the account, then global median
    behav = ['health', 'active_users', 'logins', 'tickets']
    for k in num_keys:
        if k in behav:
            df = df.sort_values([c['account'], c['month']])
            df[c[k]] = df.groupby(c['account'])[c[k]].ffill()
            df[c[k]] = df[c[k]].fillna(df[c[k]].median())
        else:
            df[c[k]] = df[c[k]].fillna(0)
    for k in ['new_logo', 'first_row', 'churn']:
        df[c[k]] = df[c[k]].astype(int)
    df[c['health']] = df[c['health']].clip(0, 100)
    # negatives where the domain forbids them
    neg = 0
    for k in config['NONNEG_KEYS']:
        m = df[c[k]] < 0
        neg += int(m.sum())
        df.loc[m, c[k]] = 0
    print('[clean] negative values clipped to 0:', neg)
    # churn reason: only meaningful on churn rows
    reason = df[c['churn_reason']].astype(str).str.strip().replace({'nan': '', 'None': ''})
    df[c['churn_reason']] = np.where(df[c['churn']] == 1, np.where(reason == '', 'Unknown', reason), 'None')
    # dedupe on account-month (keep last = latest correction)
    df = df.sort_values([c['account'], c['month']])
    before = len(df)
    df = df.drop_duplicates([c['account'], c['month']], keep='last')
    print('[clean] duplicates removed:', before - len(df))
    # cap usage and cost spikes only
    for k in config['CAP_KEYS']:
        cap = df[c[k]].quantile(config['CAP_QUANTILE'])
        n = int((df[c[k]] > cap).sum())
        df[c[k]] = df[c[k]].clip(upper=cap)
        print('[clean] capped', c[k], 'at', round(float(cap), 2), '| rows:', n)
    df['mrr_identity_gap'] = df[c['mrr_start']] + df[c['mrr_new']] + df[c['mrr_exp']] - df[c['mrr_con']] - df[c['mrr_churn']] - df[c['mrr_end']]
    df['churn_label'] = np.where(df[c['churn']] == 1, 'Churned', 'Retained')
    df = df.reset_index(drop=True)
    df.to_csv(config['PROCESSED_CSV'], index=False, encoding='utf-8')
    print('[clean] rows in:', n0, '| rows out:', len(df), '| saved', config['PROCESSED_CSV'])
    return df
