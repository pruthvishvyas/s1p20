# [NOTE] src/analytics/business.py   | OUTCOME: DECIDE (rules, simulations) + MONITOR (goals)
import os
import numpy as np
import pandas as pd
from src.utils import write_json

ACTIONS = {
    'RENEWAL_AT_RISK': 'Executive-sponsor call and renewal save-offer this week',
    'CHURN_RISK_HIGH': 'CS manager outreach within 5 days; agree an adoption recovery plan',
    'RENEWAL_WATCH': 'Start renewal conversation early; confirm champion and value delivered',
    'LOW_ADOPTION': 'Run onboarding/training session; right-size seats at renewal',
    'NEGATIVE_CONTRIBUTION': 'Reprice or cut cost-to-serve; review CAC payback for this account',
    'LOW_GROSS_MARGIN': 'Review hosting/support cost or raise price at next renewal',
    'COLLECTIONS_OVERDUE': 'Finance collections call this week; pause new discounts until cleared',
    'SUPPORT_COST_HEAVY': 'Route to self-serve resources; review ticket root causes with Product',
    'EXPANSION_READY': 'Upsell seats or move to a higher plan',
    'OVER_DISCOUNTED': 'Reduce discount at renewal; healthy account can absorb it',
    'ANOMALY_REVIEW': 'Investigate unusual usage/revenue/cost movement flagged by the model',
}
ORDER = {'P1_URGENT': 0, 'P2_HIGH': 1, 'P3_MEDIUM': 2, 'P4_ROUTINE': 3}


def assign_alerts(r, t, c):
    a, risk = [], r['risk_level']
    if risk == 'HIGH' and r['renewal_within_3m'] == 1:
        a.append('RENEWAL_AT_RISK')
    elif risk == 'HIGH':
        a.append('CHURN_RISK_HIGH')
    elif risk == 'MEDIUM' and r['renewal_within_3m'] == 1:
        a.append('RENEWAL_WATCH')
    if r['seat_utilization'] < t['utilization_low']:
        a.append('LOW_ADOPTION')
    if r['contrib_margin_3m'] < 0:
        a.append('NEGATIVE_CONTRIBUTION')
    elif r['gross_margin_pct'] < t['gross_margin_floor']:
        a.append('LOW_GROSS_MARGIN')
    if r[c['ar60']] > 0 or r['ar_days'] > t['ar_days_multiple'] * max(r[c['terms']], 1):
        a.append('COLLECTIONS_OVERDUE')
    if r['support_cost_ratio'] > t['support_cost_ratio_max']:
        a.append('SUPPORT_COST_HEAVY')
    if risk == 'LOW' and r[c['health']] >= t['health_green'] and r['seat_utilization'] >= t['utilization_high']:
        a.append('EXPANSION_READY')
    if risk != 'HIGH' and r[c['discount']] >= t['discount_cap'] and r[c['health']] >= 70:
        a.append('OVER_DISCOUNTED')
    if r.get('is_anomaly', 0) == 1:
        a.append('ANOMALY_REVIEW')
    return '|'.join(a) if a else 'NORMAL'


def priority_level(s, mrr, q75):
    if 'RENEWAL_AT_RISK' in s or ('CHURN_RISK_HIGH' in s and mrr >= q75):
        return 'P1_URGENT'
    if any(k in s for k in ['CHURN_RISK_HIGH', 'COLLECTIONS_OVERDUE', 'NEGATIVE_CONTRIBUTION', 'RENEWAL_WATCH']):
        return 'P2_HIGH'
    if any(k in s for k in ['LOW_ADOPTION', 'LOW_GROSS_MARGIN', 'OVER_DISCOUNTED', 'SUPPORT_COST_HEAVY', 'ANOMALY_REVIEW', 'EXPANSION_READY']):
        return 'P3_MEDIUM'
    return 'P4_ROUTINE'


def recommend(s):
    return '; '.join(ACTIONS[k] for k in s.split('|') if k in ACTIONS) if s != 'NORMAL' else 'No action needed'


def run_simulations(acct, config):
    c, S = config['COLS'], config['SIM']
    p = acct['churn_prob'].fillna(0).clip(0, 1).to_numpy()
    mrr = acct[c['mrr_end']].to_numpy(dtype=float)
    base = float((mrr * (1 - p)).sum())
    note = 'Assumption-driven what-if. Churn sensitivity is editable in CONFIG["SIM"]; results are expected values for next month.'
    # 1) price change
    rows = []
    for d in [-0.10, -0.05, 0.0, 0.025, 0.05, 0.075, 0.10, 0.15]:
        p2 = np.clip(p * (1 + S['price_churn_sensitivity'] * d), 0, 1)
        proj = float((mrr * (1 + d) * (1 - p2)).sum())
        rows.append({'price_change_pct': d * 100, 'expected_next_month_mrr': proj, 'delta_vs_baseline': proj - base,
                     'delta_annualised': (proj - base) * 12, 'expected_churned_logos': float(p2.sum())})
    write_json({'assumption': note, 'baseline_mrr': base, 'scenarios': rows}, config['SIM_DIR'] + 'price_change_impact.json')
    # 2) retention campaign ROI
    gm = float(np.clip(acct['gross_margin_pct'].mean(), 0.3, 0.95))
    cs = float(acct[c['cs_cost']].mean())
    cost_pa = S['campaign_cost_months_of_cs'] * (cs if cs > 0 else 150.0)
    order = acct.sort_values('churn_prob', ascending=False)
    rows = []
    for tp in S['campaign_top_pcts']:
        sub = order.head(max(1, int(len(order) * tp)))
        exp_loss = float((sub['churn_prob'].fillna(0) * sub[c['mrr_end']]).sum())
        for sr in S['campaign_save_rates']:
            value = exp_loss * sr * S['value_horizon_months'] * gm
            cost = len(sub) * cost_pa
            rows.append({'target_top_pct': tp * 100, 'accounts_targeted': len(sub), 'save_rate': sr * 100, 'campaign_cost': cost,
                         'protected_gross_profit': value, 'net_benefit': value - cost, 'roi': (value - cost) / cost if cost > 0 else None})
    write_json({'assumption': 'Save rate = share of expected churn prevented by the campaign.', 'cost_per_account': cost_pa, 'gross_margin_used': gm, 'scenarios': rows}, config['SIM_DIR'] + 'retention_campaign_roi.json')
    # 3) discount policy at renewal
    el = acct[(acct[c['discount']] > config['THRESHOLDS']['discount_cap']) & (acct['risk_level'] != 'HIGH')]
    rows = []
    pe, me = el['churn_prob'].fillna(0).clip(0, 1).to_numpy(), el[c['mrr_end']].to_numpy(dtype=float)
    for pts in [0.0, 0.025, 0.05, 0.075, 0.10]:
        cut = np.minimum(pts, el[c['discount']].to_numpy())
        extra = el[c['seats']].to_numpy() * el[c['list_price']].to_numpy() * cut
        p2 = np.clip(pe * (1 + S['price_churn_sensitivity'] * np.divide(extra, me, out=np.zeros_like(extra), where=me > 0)), 0, 1)
        delta = float(((me + extra) * (1 - p2)).sum() - (me * (1 - pe)).sum())
        rows.append({'discount_reduction_pts': pts * 100, 'eligible_accounts': int(len(el)), 'extra_mrr_if_all_stay': float(extra.sum()),
                     'expected_net_mrr_change': delta, 'expected_net_arr_change': delta * 12})
    write_json({'assumption': note, 'eligible_rule': 'discount above cap and risk not HIGH', 'scenarios': rows}, config['SIM_DIR'] + 'discount_policy_impact.json')
    print('[simulations] 3 lookup JSONs written to', config['SIM_DIR'])


def write_goals(config):
    g = {
        'mrr_target': {'value': None, 'unit': 'usd_monthly', 'client_sets': True, 'description': 'Target ending MRR; set in the dashboard'},
        'alert_mrr_drop_pct': {'value': 3, 'unit': 'percent', 'description': 'Alert if MRR falls month-over-month by more than this %'},
        'max_monthly_logo_churn_pct': {'value': 2.0, 'unit': 'percent', 'description': 'B2B SaaS benchmark: keep monthly logo churn under 2%'},
        'max_monthly_gross_revenue_churn_pct': {'value': 1.5, 'unit': 'percent', 'description': 'Churn+contraction as % of starting MRR (about 17% a year)'},
        'min_net_revenue_retention_pct': {'value': 100, 'unit': 'percent', 'description': 'Monthly NRR below 100% means the base shrinks without new sales'},
        'max_ar60_share_pct': {'value': 10, 'unit': 'percent', 'description': 'Share of receivables older than 60 days'},
        'max_high_risk_mrr_share_pct': {'value': 15, 'unit': 'percent', 'description': 'Share of MRR sitting in HIGH churn-risk accounts'},
        'min_gross_margin_pct': {'value': 70, 'unit': 'percent', 'description': 'Healthy SaaS gross margin floor'},
        'forecast_horizon': {'value': config['FORECAST_HORIZON_MONTHS'], 'unit': 'months'},
    }
    write_json(g, config['GOALS_JSON'])
    return g


def run_business_logic(df, config):
    c, t = config['COLS'], config['THRESHOLDS']
    df = df.copy()
    for col in ['alerts', 'priority', 'recommendations', 'mrr_at_risk']:
        if col in df.columns:
            df = df.drop(columns=[col])
    acct = df[(df['is_latest_month'] == 1) & (df[c['churn']] == 0)].copy()
    if 'churn_prob' not in acct.columns:
        acct['churn_prob'], acct['risk_level'] = 0.0, 'LOW'
    acct['churn_prob'] = acct['churn_prob'].fillna(0.0)
    acct['risk_level'] = acct['risk_level'].fillna('LOW')
    q75 = float(acct[c['mrr_end']].quantile(0.75)) if len(acct) else 0.0
    acct['alerts'] = acct.apply(lambda r: assign_alerts(r, t, c), axis=1)
    acct['priority'] = [priority_level(s, m, q75) for s, m in zip(acct['alerts'], acct[c['mrr_end']])]
    acct['recommendations'] = acct['alerts'].map(recommend)
    acct['mrr_at_risk'] = acct['churn_prob'] * acct[c['mrr_end']]
    acct['_o'] = acct['priority'].map(ORDER)
    acct = acct.sort_values(['_o', 'mrr_at_risk'], ascending=[True, False]).drop(columns=['_o'])
    keep = [c['account'], c['month'], c['segment'], c['plan'], c['region'], c['contract'], 'segment_name', c['mrr_end'], c['seats'],
            c['list_price'], c['discount'], c['health'], 'seat_utilization', 'gross_margin_pct', 'contrib_margin_3m', c['ar60'], 'ar_days',
            'renewal_within_3m', 'months_to_renewal', 'churn_prob', 'risk_level', 'mrr_at_risk', 'is_anomaly', 'alerts', 'priority', 'recommendations']
    acct[[k for k in keep if k in acct.columns]].to_csv(config['BIZ_CSV'], index=False, encoding='utf-8')
    df = df.merge(acct[[c['account'], c['month'], 'alerts', 'priority', 'recommendations', 'mrr_at_risk']], on=[c['account'], c['month']], how='left')
    print('[business] priority mix:', acct['priority'].value_counts().to_dict())
    print('[business] accounts with at least one alert:', int((acct['alerts'] != 'NORMAL').sum()), 'of', len(acct))
    if len(acct) >= 10:
        run_simulations(acct, config)
    else:
        print('[business] WARNING: <10 active accounts, simulations skipped')
    write_goals(config)
    print('[business] goals written to', config['GOALS_JSON'])
    return df
