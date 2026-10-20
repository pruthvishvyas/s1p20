# [NOTE] src/features/engineer.py   | OUTCOME: feeds UNDERSTAND, DECIDE and MONITOR
import numpy as np
import pandas as pd
from src.utils import safe_div


def _roll(df, key, col, win, how='mean'):
    r = df.groupby(key)[col].rolling(win, min_periods=1)
    return getattr(r, how)().reset_index(level=0, drop=True)


def engineer(df, config):
    c = config['COLS']
    a, m = c['account'], c['month']
    df = df.sort_values([a, m]).reset_index(drop=True).copy()
    g = df.groupby(a)
    # --- adoption
    df['seat_utilization'] = safe_div(df[c['active_users']], df[c['seats']]).clip(0, 1.5)
    df['logins_per_active_user'] = safe_div(df[c['logins']], df[c['active_users']])
    df['logins_per_seat'] = safe_div(df[c['logins']], df[c['seats']])
    # --- unit economics
    df['gross_margin_pct'] = safe_div(df[c['gross_profit']], df[c['revenue']]).clip(-1, 1)
    df['contribution_margin_pct'] = safe_div(df[c['contrib']], df[c['revenue']]).clip(-3, 1)
    df['_contrib'] = df[c['contrib']]
    df['_rev'] = df[c['revenue']]
    df['contrib_margin_3m'] = (safe_div(_roll(df, a, '_contrib', 3, 'sum'), _roll(df, a, '_rev', 3, 'sum'))).clip(-3, 1)
    df['cost_to_serve_ratio'] = safe_div(df[c['hosting']] + df[c['support_cost']] + df[c['cs_cost']], df[c['revenue']]).clip(0, 3)
    df['support_cost_ratio'] = safe_div(df[c['support_cost']], df[c['revenue']]).clip(0, 3)
    df['tickets_per_seat'] = safe_div(df[c['tickets']], df[c['seats']])
    df['price_realization'] = safe_div(df[c['net_price']], df[c['list_price']], fill=1.0).clip(0, 1.5)
    df['heavy_discount_flag'] = (df[c['discount']] >= config['THRESHOLDS']['discount_cap']).astype(int)
    # --- cash
    df['_inv'] = df[c['invoiced']]
    df['_cash'] = df[c['cash']]
    df['collection_rate_3m'] = safe_div(_roll(df, a, '_cash', 3, 'sum'), _roll(df, a, '_inv', 3, 'sum'), fill=1.0).clip(0, 2)
    df['ar_days'] = safe_div(df[c['ar_close']], df[c['revenue']]) * 30.0
    df['ar60_ratio'] = safe_div(df[c['ar60']], df[c['ar_close']])
    df['overdue_flag'] = (df[c['ar60']] > 0).astype(int)
    # --- contract and renewal calendar
    tmap = {k.lower(): v for k, v in config['CONTRACT_TERM_MONTHS'].items()}
    terms = df[c['contract']].astype(str).str.strip().str.lower().map(tmap)
    unknown = sorted(df.loc[terms.isnull(), c['contract']].unique().tolist())
    if unknown:
        print('[engineer] unknown contract types treated as monthly:', unknown)
    df['term_months'] = terms.fillna(1).astype(int)
    ten = df[c['tenure']].astype(int)
    df['tenure_mod_term'] = ten % df['term_months']
    df['months_to_renewal'] = (df['term_months'] - ((ten + 1) % df['term_months'])) % df['term_months']
    df['is_monthly'] = (df['term_months'] == 1).astype(int)
    df['renewal_within_3m'] = ((df['term_months'] > 1) & (df['months_to_renewal'] < config['THRESHOLDS']['renewal_window_months'])).astype(int)
    df['is_first_year'] = (ten <= 12).astype(int)
    # --- momentum (only past and present values: no look-ahead)
    df['health_change_1m'] = (df[c['health']] - g[c['health']].shift(1)).fillna(0)
    df['health_roll3'] = _roll(df, a, c['health'], 3, 'mean')
    df['health_drop_flag'] = (df['health_change_1m'] <= -10).astype(int)
    df['active_users_change_1m'] = safe_div(df[c['active_users']] - g[c['active_users']].shift(1), g[c['active_users']].shift(1)).clip(-1, 3)
    df['_prev_logins'] = g[c['logins']].shift(1)
    prior = _roll(df, a, '_prev_logins', 3, 'mean')
    df['logins_change_3m'] = (safe_div(df[c['logins']], prior, fill=1.0) - 1).clip(-1, 5)
    df['tickets_roll3'] = _roll(df, a, c['tickets'], 3, 'sum')
    df['mrr_growth_3m'] = safe_div(df[c['mrr_end']] - g[c['mrr_end']].shift(3), g[c['mrr_end']].shift(3)).clip(-1, 5)
    df['_exp_flag'] = (df[c['mrr_exp']] > 0).astype(int)
    df['_con_flag'] = (df[c['mrr_con']] > 0).astype(int)
    df['expansion_6m'] = _roll(df, a, '_exp_flag', 6, 'sum')
    df['contraction_6m'] = _roll(df, a, '_con_flag', 6, 'sum')
    df['log_mrr'] = np.log1p(df[c['mrr_end']])
    df['log_seats'] = np.log1p(df[c['seats']])
    # --- target: does this ACTIVE account churn in the very next month?
    pn = df[m].dt.year * 12 + df[m].dt.month
    nxt = g[c['churn']].shift(-1)
    nxt_p = pn.groupby(df[a]).shift(-1)
    valid = nxt.notna() & ((nxt_p - pn) == 1) & (df[c['churn']] == 0)
    df['churn_next_month'] = np.where(valid, nxt, np.nan)
    df['label_valid'] = valid.astype(int)
    df['is_latest_month'] = (df[m] == df[m].max()).astype(int)
    df = df.drop(columns=[x for x in df.columns if x.startswith('_')])
    df = df.replace([np.inf, -np.inf], np.nan)
    miss = [f for f in config['MODEL_ENG_FEATURES'] if f not in df.columns]
    if miss:
        raise ValueError('engineered features missing: ' + str(miss))
    df[config['MODEL_ENG_FEATURES']] = df[config['MODEL_ENG_FEATURES']].fillna(0)
    df.to_csv(config['FEAT_CSV'], index=False, encoding='utf-8')
    print('[engineer] features:', len(config['MODEL_ENG_FEATURES']), '| labeled rows:', int(df['label_valid'].sum()),
          '| next-month churn rate:', round(float(df.loc[df['label_valid'] == 1, 'churn_next_month'].mean()), 4))
    print('[engineer] saved feature store ->', config['FEAT_CSV'])
    return df
