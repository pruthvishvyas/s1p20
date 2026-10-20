# [NOTE] src/reporting/export.py   | OUTCOME: UNDERSTAND / DECIDE / MONITOR (client-facing Excel + dashboard)
import os
import numpy as np
import pandas as pd
from src.utils import monthly_summary


def export(df, config):
    c = config['COLS']
    R = config['REPORTS_DIR']
    ms = monthly_summary(df, c)
    biz = pd.read_csv(config['BIZ_CSV'], keep_default_na=False, na_values=['']) if os.path.exists(config['BIZ_CSV']) else pd.DataFrame()
    fc = pd.read_csv(config['FORECAST_CSV']) if os.path.exists(config['FORECAST_CSV']) else pd.DataFrame()
    rev = ms[['month', 'mrr_start', 'mrr_new', 'mrr_exp', 'mrr_con', 'mrr_churn', 'mrr_end', 'net_new_mrr', 'logo_churn_rate', 'grr', 'nrr', 'gross_margin_pct']].copy()
    rev['month'] = rev['month'].dt.strftime('%Y-%m')
    rev.columns = ['Month', 'Starting MRR', 'New MRR', 'Expansion MRR', 'Contraction MRR', 'Churned MRR', 'Ending MRR', 'Net New MRR', 'Logo Churn Rate', 'Gross Revenue Retention', 'Net Revenue Retention', 'Gross Margin']
    path = R + config['CLIENT_ID'] + '_report.xlsx'
    with pd.ExcelWriter(path, engine='openpyxl') as xw:
        rev.to_excel(xw, sheet_name='Revenue Summary', index=False)
        if len(biz):
            biz.to_excel(xw, sheet_name='Account Health', index=False)
            biz[biz['risk_level'].isin(['HIGH', 'MEDIUM'])].sort_values('mrr_at_risk', ascending=False).to_excel(xw, sheet_name='Churn Risk List', index=False)
            biz[biz['alerts'] != 'NORMAL'][[c['account'], 'priority', 'alerts', 'recommendations', c['mrr_end'], 'mrr_at_risk']].to_excel(xw, sheet_name='Action List', index=False)
            biz[biz[c['ar60']] > 0].sort_values(c['ar60'], ascending=False).to_excel(xw, sheet_name='Cash and Collections', index=False)
        if len(fc):
            fc.to_excel(xw, sheet_name='MRR Forecast', index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = 'A2'
            for col in ws.columns:
                width = max(len(str(col[0].value or '')), 10) + 2
                ws.column_dimensions[col[0].column_letter].width = min(width, 45)
    try:
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        fig = make_subplots(rows=2, cols=2, subplot_titles=('MRR and forecast', 'Monthly logo churn %', 'MRR by churn risk level', 'Accounts by priority'))
        fig.add_trace(go.Scatter(x=ms['month'], y=ms['mrr_end'], name='MRR'), row=1, col=1)
        if len(fc):
            fig.add_trace(go.Scatter(x=fc['month'], y=fc['mrr_p50'], name='Forecast P50'), row=1, col=1)
        fig.add_trace(go.Scatter(x=ms['month'], y=ms['logo_churn_rate'] * 100, name='Logo churn %'), row=1, col=2)
        if len(biz):
            rk = biz.groupby('risk_level')[c['mrr_end']].sum().reset_index()
            fig.add_trace(go.Bar(x=rk['risk_level'], y=rk[c['mrr_end']], name='MRR'), row=2, col=1)
            pr = biz['priority'].value_counts().sort_index().reset_index()
            fig.add_trace(go.Bar(x=pr.iloc[:, 0], y=pr.iloc[:, 1], name='Accounts'), row=2, col=2)
        fig.update_layout(title=config['CLIENT_NAME'] + ' - interactive dashboard', height=760, showlegend=False)
        fig.write_html(R + 'interactive_dashboard.html')
    except Exception as e:
        print('[export] interactive dashboard skipped:', e)
    last = ms.iloc[-1]
    print('=' * 60)
    print(config['CLIENT_NAME'], '- SUMMARY')
    print('Ending MRR: $%s | ARR: $%s | active accounts: %d' % (format(last['mrr_end'], ',.0f'), format(last['mrr_end'] * 12, ',.0f'), int(last['accounts_end'])))
    print('Logo churn (last month): %.2f%% | NRR: %.1f%% | GRR: %.1f%%' % (last['logo_churn_rate'] * 100, last['nrr'] * 100, last['grr'] * 100))
    if len(biz):
        print('HIGH-risk accounts: %d | P1 urgent: %d | expected MRR at risk: $%s' % ((biz['risk_level'] == 'HIGH').sum(), (biz['priority'] == 'P1_URGENT').sum(), format(biz['mrr_at_risk'].sum(), ',.0f')))
    print('Excel report ->', path)
    print('=' * 60)
