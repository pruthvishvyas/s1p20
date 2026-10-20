# [NOTE] src/analytics/insights.py   | OUTCOME: DECIDE
import os
import numpy as np
import pandas as pd
from src.utils import write_json, monthly_summary


def run_insights(df, config):
    c, t, S = config['COLS'], config['THRESHOLDS'], config['SIM']
    acct = df[(df['is_latest_month'] == 1) & (df[c['churn']] == 0)].copy()
    acct['churn_prob'] = acct['churn_prob'].fillna(0) if 'churn_prob' in acct.columns else 0.0
    if 'risk_level' not in acct.columns:
        acct['risk_level'] = 'LOW'
    if 'alerts' not in acct.columns:
        acct['alerts'] = 'NORMAL'
    tot_mrr = float(acct[c['mrr_end']].sum())
    ms = monthly_summary(df, c)
    items = []

    def add(cat, finding, evidence, action, impact):
        items.append({'category': cat, 'finding': finding, 'evidence': evidence, 'action': action, 'outcome': 'DECIDE', 'impact_usd_monthly': float(impact)})

    def has(a):
        return acct['alerts'].str.contains(a, regex=False)

    def block(fn):
        try:
            fn()
        except Exception as e:
            print('[insights] skipped one insight:', e)

    def i_risk():
        hi = acct[acct['risk_level'] == 'HIGH']
        loss = float((hi['churn_prob'] * hi[c['mrr_end']]).sum())
        add('Churn Risk', str(len(hi)) + ' accounts (' + format(len(hi) / max(len(acct), 1), '.0%') + ' of the base) are HIGH churn risk and carry $' + format(hi[c['mrr_end']].sum(), ',.0f') + ' MRR.',
            'Expected MRR lost next month from this group: $' + format(loss, ',.0f') + '; total active MRR $' + format(tot_mrr, ',.0f') + '.',
            'CS lead works the Churn Risk List top-down this week; every HIGH account gets a named owner and a call.', hi[c['mrr_end']].sum())

    def i_renew():
        r = acct[has('RENEWAL_AT_RISK') | has('RENEWAL_WATCH')]
        if len(r) == 0:
            return
        add('Renewal Risk', str(len(r)) + ' contracts renew within ' + str(t['renewal_window_months']) + ' months with elevated churn risk ($' + format(r[c['mrr_end']].sum(), ',.0f') + ' MRR).',
            'Annual-style contracts churn at renewal; ' + str(int(has('RENEWAL_AT_RISK').sum())) + ' are HIGH risk right now.',
            'Start renewal conversations now; prepare a save offer for the RENEWAL_AT_RISK accounts.', r[c['mrr_end']].sum())

    def i_cash():
        a60 = float(acct[c['ar60']].sum())
        n = int((acct[c['ar60']] > 0).sum())
        if a60 <= 0:
            return
        add('Cash and Collections', '$' + format(a60, ',.0f') + ' of receivables are 60+ days old across ' + str(n) + ' accounts.',
            'AR 60+ share of closing AR: ' + format(float(ms['ar60_share'].iloc[-1]), '.1%') + ' (goal under 10%).',
            'Finance runs a collections sprint on the COLLECTIONS_OVERDUE list; pause discounts for those accounts.', a60)

    def i_margin():
        neg = acct[acct['contrib_margin_3m'] < 0]
        if len(neg) == 0:
            return
        loss = float(-(neg['contrib_margin_3m'] * neg[c['mrr_end']]).sum())
        add('Profitability', str(len(neg)) + ' accounts have negative 3-month contribution margin after CAC and cost-to-serve.',
            'They represent ' + format(neg[c['mrr_end']].sum() / max(tot_mrr, 1), '.1%') + ' of MRR; estimated monthly contribution leak $' + format(loss, ',.0f') + '.',
            'Reprice at renewal or cut support/hosting cost for these accounts; check CAC payback on new deals in this profile.', loss)

    def i_reason():
        r = df[df[c['churn']] == 1].groupby(c['churn_reason'])[c['mrr_churn']].sum().sort_values(ascending=False)
        top = r.index[0]
        add('Retention', 'Top churn reason by lost MRR is "' + str(top) + '" (' + format(r.iloc[0] / max(r.sum(), 1), '.0%') + ' of all churned MRR).',
            'Churned MRR to date: $' + format(r.sum(), ',.0f') + '; top reason $' + format(r.iloc[0], ',.0f') + '.',
            'Assign Product/CS an owner for this reason and review the accounts showing the same early signals.', r.iloc[0] / max(df[c['month']].nunique(), 1))

    def i_group():
        overall = float(df[c['churn']].mean())
        best = None
        for k in ['plan', 'contract', 'segment', 'channel', 'industry', 'region']:
            g = df.groupby(c[k])[c['churn']].agg(['mean', 'count'])
            g = g[g['count'] >= 200]
            if len(g):
                top = g['mean'].idxmax()
                lift = g.loc[top, 'mean'] / max(overall, 1e-9)
                if best is None or lift > best[3]:
                    best = (k, top, g.loc[top, 'mean'], lift)
        k, top, rate, lift = best
        grp_mrr = float(acct.loc[acct[c[k]] == top, c['mrr_end']].sum())
        add('Retention', c[k] + ' "' + str(top) + '" churns at ' + format(rate, '.2%') + ' per month, ' + format(lift, '.1f') + 'x the company average.',
            'Company average ' + format(overall, '.2%') + '; this group holds $' + format(grp_mrr, ',.0f') + ' of current MRR.',
            'Review onboarding, pricing and fit for this group before spending more acquisition budget on it.', grp_mrr * max(rate - overall, 0))

    def i_adopt():
        lab = df[df['label_valid'] == 1]
        low = lab[lab['seat_utilization'] < t['utilization_low']]
        ok = lab[lab['seat_utilization'] >= t['utilization_low']]
        cur = acct[acct['seat_utilization'] < t['utilization_low']]
        add('Product Adoption', 'Accounts using under ' + format(t['utilization_low'], '.0%') + ' of paid seats churn next month at ' + format(low['churn_next_month'].mean(), '.2%') + ' vs ' + format(ok['churn_next_month'].mean(), '.2%') + ' for the rest.',
            str(len(cur)) + ' active accounts ($' + format(cur[c['mrr_end']].sum(), ',.0f') + ' MRR) are below the threshold today.',
            'Run seat-activation / training sessions for these accounts; right-size seats at renewal rather than lose the logo.', cur[c['mrr_end']].sum() * float(low['churn_next_month'].mean()))

    def i_expand():
        e = acct[has('EXPANSION_READY')]
        if len(e) == 0:
            return
        up = float(e[c['mrr_end']].sum() * S['expansion_uplift_pct'])
        add('Expansion', str(len(e)) + ' healthy, fully adopted, low-risk accounts are ready for an upsell.',
            'Current MRR $' + format(e[c['mrr_end']].sum(), ',.0f') + '; a ' + format(S['expansion_uplift_pct'], '.0%') + ' uplift assumption is worth about $' + format(up, ',.0f') + ' MRR.',
            'Sales/CS offers extra seats or the next plan tier to this list this month.', up)

    def i_disc():
        d = acct[has('OVER_DISCOUNTED')]
        if len(d) == 0:
            return
        up = float((d[c['seats']] * d[c['list_price']] * 0.05).sum())
        add('Pricing', str(len(d)) + ' healthy accounts get more than ' + format(t['discount_cap'], '.0%') + ' off list price.',
            'Cutting 5 discount points at renewal adds about $' + format(up, ',.0f') + ' MRR if they all stay (see discount_policy_impact simulation).',
            'Cap renewal discounts for healthy accounts; approve deeper discounts only with a documented reason.', up)

    def i_trend():
        l3, p3 = float(ms['net_new_mrr'].tail(3).mean()), float(ms['net_new_mrr'].iloc[-6:-3].mean()) if len(ms) >= 6 else float('nan')
        fc = pd.read_csv(config['FORECAST_CSV']) if os.path.exists(config['FORECAST_CSV']) else None
        ev = 'Average net new MRR last 3 months $' + format(l3, ',.0f') + ' vs prior 3 months $' + format(p3, ',.0f') + '.'
        if fc is not None and len(fc):
            ev += ' Forecast MRR in ' + str(len(fc)) + ' months (P50): $' + format(fc['mrr_p50'].iloc[-1], ',.0f') + '.'
        add('Revenue Health', 'Net new MRR is running at $' + format(l3, ',.0f') + ' per month.', ev,
            'If net new MRR is falling, shift effort from acquisition to expansion and saves; track it weekly.', abs(l3))

    def i_conc():
        top = acct.sort_values(c['mrr_end'], ascending=False).head(max(1, int(len(acct) * 0.10)))
        add('Concentration Risk', 'The top 10% of accounts generate ' + format(top[c['mrr_end']].sum() / max(tot_mrr, 1), '.0%') + ' of MRR.',
            'Expected MRR loss among these accounts next month: $' + format((top['churn_prob'] * top[c['mrr_end']]).sum(), ',.0f') + '.',
            'Give every top-decile account an executive sponsor and a quarterly business review.', (top['churn_prob'] * top[c['mrr_end']]).sum())

    def i_anom():
        recent = df[(df['is_anomaly'] == 1) & (df[c['month']] >= df[c['month']].max() - pd.offsets.MonthBegin(2))]
        drv = recent['anomaly_driver'].str.split(' ').str[0].value_counts()
        add('Anomaly Watch', str(len(recent)) + ' account-months were flagged as unusual in the last 3 months.',
            'Most common driver: ' + (str(drv.index[0]) if len(drv) else 'n/a') + '.',
            'CS ops reviews the Anomaly Explorer weekly and confirms whether each case is real churn signal or data error.', 0.0)

    for fn in [i_risk, i_renew, i_cash, i_margin, i_reason, i_group, i_adopt, i_expand, i_disc, i_trend, i_conc, i_anom]:
        block(fn)
    items.sort(key=lambda x: -x['impact_usd_monthly'])
    for i, it in enumerate(items):
        it['severity'] = 'HIGH' if i < 3 else ('MEDIUM' if i < 7 else 'LOW')
        it['rank'] = i + 1
    items = [{k: it[k] for k in ['severity', 'category', 'finding', 'evidence', 'action', 'outcome', 'impact_usd_monthly', 'rank']} for it in items]
    write_json(items, config['INSIGHTS_JSON'])
    for it in items:
        print('[' + it['severity'] + '] ' + it['category'] + ': ' + it['finding'])
    print('[insights]', len(items), 'insights saved ->', config['INSIGHTS_JSON'], '(severity ranked by dollar impact)')
