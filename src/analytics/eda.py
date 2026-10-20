# [NOTE] src/analytics/eda.py   | OUTCOME: charts 1-3 UNDERSTAND, 4-7 DECIDE, 8 MONITOR
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils import monthly_summary, save_fig

CHARTS = []


def run_eda(df, config):
    c = config['COLS']
    R = config['REPORTS_DIR']
    plt.rcParams.update({'figure.dpi': 100, 'axes.spines.top': False, 'axes.spines.right': False})
    ms = monthly_summary(df, c)
    x = ms['month'].dt.strftime('%Y-%m')
    pos = np.arange(len(ms))
    step = max(1, len(ms) // 12)

    # 1 UNDERSTAND: is MRR growing and what moves it?
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(pos, ms['mrr_new'], color='#2a9d8f', label='New')
    ax.bar(pos, ms['mrr_exp'], bottom=ms['mrr_new'], color='#8ab17d', label='Expansion')
    ax.bar(pos, -ms['mrr_con'], color='#e9c46a', label='Contraction')
    ax.bar(pos, -ms['mrr_churn'] - ms['mrr_con'] + ms['mrr_con'], bottom=-ms['mrr_con'], color='#e76f51', label='Churn')
    ax.set_xticks(pos[::step]); ax.set_xticklabels(x[::step], rotation=45)
    ax.set_ylabel('MRR movement ($)')
    ax2 = ax.twinx(); ax2.plot(pos, ms['mrr_end'], color='#264653', lw=2.5, label='Ending MRR'); ax2.set_ylabel('Ending MRR ($)')
    ax.legend(loc='upper left', ncol=4, fontsize=8); ax.set_title('Q1 [UNDERSTAND] Is MRR growing and what drives the change?')
    save_fig(fig, R + 'eda_01_mrr_bridge.png')

    # 2 UNDERSTAND: is churn getting worse?
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(pos, ms['logo_churn_rate'] * 100, marker='o', color='#e76f51', label='Logo churn %')
    ax.plot(pos, ms['gross_revenue_churn'] * 100, marker='s', color='#264653', label='Gross revenue churn % (churn+contraction)')
    ax.set_xticks(pos[::step]); ax.set_xticklabels(x[::step], rotation=45); ax.set_ylabel('% of starting base')
    ax.legend(); ax.set_title('Q2 [UNDERSTAND] Is churn getting worse month over month?')
    save_fig(fig, R + 'eda_02_churn_trend.png')

    # 3 UNDERSTAND: which accounts carry the revenue?
    last = df[(df[c['month']] == df[c['month']].max()) & (df[c['churn']] == 0)].sort_values(c['mrr_end'], ascending=False)
    cum = last[c['mrr_end']].cumsum() / max(last[c['mrr_end']].sum(), 1)
    n80 = int((cum < 0.8).sum() + 1)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(np.arange(1, len(cum) + 1) / max(len(cum), 1) * 100, cum.values * 100, color='#264653', lw=2)
    ax.axhline(80, ls='--', color='grey'); ax.set_xlabel('% of accounts (largest first)'); ax.set_ylabel('% of MRR')
    ax.set_title('Q3 [UNDERSTAND] Which accounts drive 80% of MRR? Top ' + str(n80) + ' of ' + str(len(cum)))
    save_fig(fig, R + 'eda_03_mrr_concentration.png')

    # 4 DECIDE: which customer groups churn most?
    piv = df.pivot_table(index=c['segment'], columns=c['plan'], values=c['churn'], aggfunc='mean') * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.heatmap(piv, annot=True, fmt='.1f', cmap='RdYlGn_r', ax=ax, cbar_kws={'label': 'monthly churn %'})
    ax.set_title('Q4 [DECIDE] Which segment x plan combinations churn most?')
    save_fig(fig, R + 'eda_04_churn_heatmap.png')

    # 5 DECIDE: why do we lose revenue?
    lost = df[df[c['churn']] == 1].groupby(c['churn_reason'])[c['mrr_churn']].sum().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    if len(lost):
        ax.barh(lost.index, lost.values, color='#e76f51')
    ax.set_xlabel('Churned MRR ($)'); ax.set_title('Q5 [DECIDE] Which churn reasons cost the most MRR?')
    save_fig(fig, R + 'eda_05_churn_reasons.png')

    # 6 DECIDE: which segments are unprofitable after cost-to-serve and CAC?
    s = df.groupby(c['segment'])[[c['revenue'], c['gross_profit'], c['contrib']]].sum()
    gm = s[c['gross_profit']] / s[c['revenue']].replace(0, np.nan) * 100
    cm = s[c['contrib']] / s[c['revenue']].replace(0, np.nan) * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    idx = np.arange(len(s))
    ax.bar(idx - 0.2, gm.values, 0.4, label='Gross margin %', color='#2a9d8f')
    ax.bar(idx + 0.2, cm.values, 0.4, label='Contribution margin % (after CAC)', color='#e9c46a')
    ax.axhline(config['THRESHOLDS']['gross_margin_floor'] * 100, ls='--', color='grey')
    ax.set_xticks(idx); ax.set_xticklabels(s.index); ax.legend(); ax.set_title('Q6 [DECIDE] Which segments are unprofitable after CAC?')
    save_fig(fig, R + 'eda_06_segment_profitability.png')

    # 7 DECIDE: does health score separate accounts that churn next month?
    lab = df[df['label_valid'] == 1]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for val, col, name in [(0, '#2a9d8f', 'Stays'), (1, '#e76f51', 'Churns next month')]:
        sub = lab.loc[lab['churn_next_month'] == val, c['health']]
        if len(sub):
            ax.hist(sub, bins=25, alpha=0.6, color=col, density=True, label=name)
    ax.axvline(config['THRESHOLDS']['health_red'], ls='--', color='grey'); ax.legend()
    ax.set_xlabel('Health score'); ax.set_title('Q7 [DECIDE] Does health score warn us before accounts churn?')
    save_fig(fig, R + 'eda_07_health_vs_churn.png')

    # 8 MONITOR: are collections slipping?
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(pos, ms['ar60_share'] * 100, marker='o', color='#264653')
    ax.set_xticks(pos[::step]); ax.set_xticklabels(x[::step], rotation=45); ax.set_ylabel('AR 60+ days as % of AR')
    ax.set_title('Q8 [MONITOR] Are collections slipping?')
    save_fig(fig, R + 'eda_08_ar_aging.png')
    print('[eda] 8 charts saved to', R, '| months:', len(ms))
