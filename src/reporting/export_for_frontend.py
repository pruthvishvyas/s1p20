# [NOTE] src/reporting/export_for_frontend.py   | read-and-package step: writes output/{understand,decide,monitor,meta}
import os, sys, json, datetime
import numpy as np
import pandas as pd
from config.config import CONFIG
from src.utils import write_json, read_json, monthly_summary, load_csv

_HERE = os.path.dirname(os.path.abspath(globals().get('__file__', 'export_for_frontend.py')))


def _bigquery_available():
    creds = os.path.join(_HERE, CONFIG['BIGQUERY']['credentials_file'])
    if not os.path.exists(creds):
        return False
    try:
        from google.cloud import bigquery  # noqa
        return True
    except ImportError:
        return False


def _load_from_csv(config):
    return load_csv(config['FEAT_CSV'], [config['COLS']['month']])


def _load_from_bigquery(config):
    from google.cloud import bigquery
    client = bigquery.Client.from_service_account_json(os.path.join(_HERE, config['BIGQUERY']['credentials_file']))
    b = config['BIGQUERY']
    df = client.query('SELECT * FROM `' + b['project_id'] + '.' + b['dataset'] + '.' + b['table'] + '`').to_dataframe()
    df[config['COLS']['month']] = pd.to_datetime(df[config['COLS']['month']])
    return df


def _load_data(config):
    if _bigquery_available():
        try:
            df = _load_from_bigquery(config)
            print('[export_for_frontend] Source: BigQuery')
            return df, 'bigquery'
        except Exception as e:
            print('[export_for_frontend] WARNING BigQuery failed (' + str(e) + '); falling back to CSV')
    print('[export_for_frontend] Source: CSV')
    return _load_from_csv(config), 'csv'


def _rd(p):
    return pd.read_csv(p, keep_default_na=False, na_values=['']) if os.path.exists(p) else pd.DataFrame()


def main():
    cfg = CONFIG
    c, O = cfg['COLS'], cfg['OUTPUT_DIR']
    df, source = _load_data(cfg)
    ms = monthly_summary(df, c)
    last = ms.iloc[-1]
    prev = ms.iloc[-2] if len(ms) > 1 else last
    goals, val, met = read_json(cfg['GOALS_JSON'], {}), read_json(cfg['VALIDATION_JSON'], {}), read_json(cfg['METRICS_JSON'], {})
    biz, fc, seg, anom = _rd(cfg['BIZ_CSV']), _rd(cfg['FORECAST_CSV']), _rd(cfg['SEGMENTS_CSV']), _rd(cfg['ML2_CSV'])
    snap = df[(df[c['month']] == df[c['month']].max()) & (df[c['churn']] == 0)]
    files = []

    def out(rel, obj, purpose, outcome):
        write_json(obj, O + rel)
        files.append({'filename': rel, 'purpose': purpose, 'outcome': outcome})

    def tail_prod(col):
        t = ms.tail(12)
        return float(np.prod(t[col])) * 100 if len(t) >= 12 else None

    hi = biz[biz['risk_level'] == 'HIGH'] if len(biz) else pd.DataFrame()
    mrr_now = float(last['mrr_end'])
    kpis = {
        'as_of': str(last['month'])[:10], 'mrr': mrr_now, 'arr': mrr_now * 12, 'active_accounts': int(last['accounts_end']),
        'new_logos_last_month': int(last['new_logos']), 'churned_logos_last_month': int(last['churned_logos']),
        'logo_churn_rate_pct': float(last['logo_churn_rate']) * 100, 'nrr_monthly_pct': float(last['nrr']) * 100,
        'grr_monthly_pct': float(last['grr']) * 100, 'nrr_trailing12_pct': tail_prod('nrr'), 'grr_trailing12_pct': tail_prod('grr'),
        'mrr_mom_pct': (mrr_now / float(prev['mrr_end']) - 1) * 100 if float(prev['mrr_end']) > 0 and len(ms) > 1 else 0.0,
        'gross_margin_pct': float(last['gross_margin_pct']) * 100, 'contribution_margin_pct': float(last['contribution_margin_pct']) * 100,
        'ar_closing': float(last['ar_close']), 'ar_60plus': float(last['ar60']), 'ar60_share_pct': float(last['ar60_share']) * 100,
        'avg_health_score': float(snap[c['health']].mean()) if len(snap) else None,
        'high_risk_accounts': int(len(hi)), 'high_risk_mrr_share_pct': float(hi[c['mrr_end']].sum()) / max(mrr_now, 1) * 100 if len(hi) else 0.0,
        'expected_mrr_at_risk': float(biz['mrr_at_risk'].sum()) if len(biz) else 0.0,
        'data_health': {k: val.get(k) for k in ['rows', 'accounts', 'months', 'first_month', 'last_month', 'duplicate_account_months', 'account_month_gaps', 'mrr_identity_mismatch_rows', 'quality_gates']},
    }
    out('understand/kpis.json', kpis, 'KPI overview cards and data health', 'UNDERSTAND')

    charts = []

    def chart(cid, title, typ, xl, yl, outcome, labels, values):
        spec = {'id': cid, 'title': title, 'type': typ, 'x_label': xl, 'y_label': yl, 'outcome': outcome,
                'data': [{'label': str(a), 'value': float(b)} for a, b in zip(labels, values)]}
        charts.append(spec)
        out('understand/charts/' + cid + '.json', spec, title, outcome)

    mlab = ms['month'].dt.strftime('%Y-%m')
    chart('mrr_trend', 'Ending MRR by month', 'line', 'Month', 'MRR ($)', 'UNDERSTAND', mlab, ms['mrr_end'])
    chart('net_new_mrr', 'Net new MRR by month', 'bar', 'Month', 'MRR ($)', 'UNDERSTAND', mlab, ms['net_new_mrr'])
    chart('logo_churn_rate', 'Monthly logo churn %', 'line', 'Month', '%', 'UNDERSTAND', mlab, ms['logo_churn_rate'] * 100)
    sg = snap.groupby(c['segment'])[c['mrr_end']].sum().sort_values(ascending=False)
    chart('mrr_by_segment', 'MRR by ' + cfg['TERMINOLOGY']['customer'].lower() + ' segment', 'bar', 'Segment', 'MRR ($)', 'UNDERSTAND', sg.index, sg.values)
    rs = df[df[c['churn']] == 1].groupby(c['churn_reason'])[c['mrr_churn']].sum().sort_values(ascending=False)
    if len(rs):
        chart('churn_reason_mrr', 'Churned MRR by reason', 'bar', 'Reason', 'MRR ($)', 'DECIDE', rs.index, rs.values)
    cp = (df.groupby(c['plan'])[c['churn']].mean() * 100).sort_values(ascending=False)
    chart('churn_rate_by_plan', 'Monthly churn % by plan', 'bar', 'Plan', '%', 'DECIDE', cp.index, cp.values)
    if len(biz):
        rk = biz.groupby('risk_level')[c['mrr_end']].sum()
        chart('mrr_by_risk_level', 'MRR by churn risk level', 'bar', 'Risk level', 'MRR ($)', 'DECIDE', rk.index, rk.values)
    imp = read_json(cfg['IMPORTANCE_JSON'], {}).get('features', [])
    if imp:
        chart('top_churn_drivers', 'Top churn drivers', 'bar', 'Feature', 'Importance', 'DECIDE', [i['feature'] for i in imp[:10]], [i['importance'] for i in imp[:10]])
    chart('ar60_share', 'Receivables older than 60 days (% of AR)', 'line', 'Month', '%', 'MONITOR', mlab, ms['ar60_share'] * 100)
    if len(fc):
        chart('forecast_mrr', 'MRR forecast (P50)', 'line', 'Month', 'MRR ($)', 'MONITOR', fc['month'].astype(str).str[:7], fc['mrr_p50'])

    if len(seg):
        g = seg.groupby('segment_name').agg(accounts=(c['account'], 'count'), mrr=(c['mrr_end'], 'sum'), avg_health=(c['health'], 'mean'), avg_utilization=('seat_utilization', 'mean')).reset_index()
        out('understand/segments.json', {'segments': g.to_dict('records'), 'accounts': seg.head(2000).to_dict('records')}, 'Segment Explorer', 'UNDERSTAND')
    else:
        out('understand/segments.json', {'segments': [], 'accounts': []}, 'Segment Explorer (insufficient data)', 'UNDERSTAND')
    if len(anom):
        a = anom.sort_values('anomaly_score', ascending=False).head(300)
        out('understand/anomalies.json', {'total_flagged': int(len(anom)), 'items': a.to_dict('records')}, 'Anomaly Explorer', 'UNDERSTAND')
    else:
        out('understand/anomalies.json', {'total_flagged': 0, 'items': []}, 'Anomaly Explorer', 'UNDERSTAND')

    ins = read_json(cfg['INSIGHTS_JSON'], [])
    out('decide/insights.json', ins, 'Insights tab', 'DECIDE')
    if len(biz):
        act = biz[biz['alerts'] != 'NORMAL']
        ac = {}
        for s in act['alerts']:
            for k in s.split('|'):
                ac[k] = ac.get(k, 0) + 1
        out('decide/recommendations.json', {'priority_counts': biz['priority'].value_counts().to_dict(), 'alert_counts': ac, 'items': act.head(500).to_dict('records')}, 'Recommendation engine', 'DECIDE')
    else:
        out('decide/recommendations.json', {'priority_counts': {}, 'alert_counts': {}, 'items': []}, 'Recommendation engine', 'DECIDE')
    for nm in ['price_change_impact', 'retention_campaign_roi', 'discount_policy_impact']:
        d = read_json(cfg['SIM_DIR'] + nm + '.json')
        if d is not None:
            out('decide/simulations/' + nm + '.json', d, 'What-If Simulator lookup: ' + nm, 'DECIDE')
    out('decide/goals.json', goals, 'Goal Tracker config (client sets targets)', 'DECIDE')

    fcj = {'horizon_months': cfg['FORECAST_HORIZON_MONTHS'], 'history': [{'month': str(m)[:10], 'mrr': float(v)} for m, v in zip(ms['month'].tail(24), ms['mrr_end'].tail(24))], 'forecast': fc.to_dict('records') if len(fc) else []}
    try:
        import joblib
        fm = joblib.load(cfg['FORECAST_MODEL']); fcj.update({'method': fm['method'], 'backtest': fm['backtest'], 'low_confidence': fm['low_confidence']})
    except Exception:
        pass
    out('monitor/forecast.json', fcj, 'Forecaster', 'MONITOR')

    def gv(k):
        return (goals.get(k) or {}).get('value')
    checks = [
        ('mrr_target', 'Ending MRR', mrr_now, gv('mrr_target'), 'min'),
        ('max_monthly_logo_churn_pct', 'Monthly logo churn %', kpis['logo_churn_rate_pct'], gv('max_monthly_logo_churn_pct'), 'max'),
        ('max_monthly_gross_revenue_churn_pct', 'Monthly gross revenue churn %', float(last['gross_revenue_churn']) * 100, gv('max_monthly_gross_revenue_churn_pct'), 'max'),
        ('min_net_revenue_retention_pct', 'Monthly NRR %', kpis['nrr_monthly_pct'], gv('min_net_revenue_retention_pct'), 'min'),
        ('max_ar60_share_pct', 'AR 60+ share %', kpis['ar60_share_pct'], gv('max_ar60_share_pct'), 'max'),
        ('max_high_risk_mrr_share_pct', 'MRR in HIGH-risk accounts %', kpis['high_risk_mrr_share_pct'], gv('max_high_risk_mrr_share_pct'), 'max'),
        ('min_gross_margin_pct', 'Gross margin %', kpis['gross_margin_pct'], gv('min_gross_margin_pct'), 'min'),
    ]
    prog, alerts = [], []
    for key, label, actual, target, kind in checks:
        if target is None:
            prog.append({'goal': key, 'label': label, 'actual': actual, 'target': None, 'status': 'not_set'}); continue
        breach = actual > target if kind == 'max' else actual < target
        prog.append({'goal': key, 'label': label, 'actual': actual, 'target': target, 'status': 'breach' if breach else 'on_track'})
        if breach:
            sev = 'HIGH' if (actual > 1.5 * target if kind == 'max' else actual < 0.9 * target) else 'MEDIUM'
            alerts.append({'severity': sev, 'goal': key, 'message': label + ' is ' + format(actual, ',.2f') + ' against a goal of ' + format(target, ',.2f'), 'outcome': 'MONITOR'})
    drop = gv('alert_mrr_drop_pct')
    if drop is not None and kpis['mrr_mom_pct'] < -drop:
        alerts.append({'severity': 'HIGH', 'goal': 'alert_mrr_drop_pct', 'message': 'MRR fell ' + format(-kpis['mrr_mom_pct'], '.1f') + '% month over month', 'outcome': 'MONITOR'})
    if len(biz):
        p1 = int((biz['priority'] == 'P1_URGENT').sum())
        if p1:
            alerts.append({'severity': 'HIGH', 'goal': 'p1_accounts', 'message': str(p1) + ' accounts need urgent action this week', 'outcome': 'MONITOR'})
    out('monitor/goal_progress.json', {'as_of': kpis['as_of'], 'goals': prog}, 'Goal progress vs actuals', 'MONITOR')
    out('monitor/alerts.json', {'as_of': kpis['as_of'], 'alerts': alerts}, 'Alert Center', 'MONITOR')

    now = datetime.datetime.now().isoformat(timespec='seconds')
    out('meta/summary.json', {'project': cfg['CLIENT_NAME'], 'domain': cfg['DOMAIN'], 'client_id': cfg['CLIENT_ID'], 'last_run': now, 'data_as_of': kpis['as_of'], 'source': source}, 'Project summary', 'META')
    out('meta/terminology.json', cfg['TERMINOLOGY'], 'Client business language', 'META')
    rl_path = O + 'meta/run_log.json'
    log = read_json(rl_path, [])
    log.append({'timestamp': now, 'source': source, 'files_written': len(files) + 1, 'rows': int(len(df)), 'status': 'ok'})
    write_json(log[-50:], rl_path)
    files.append({'filename': 'meta/run_log.json', 'purpose': 'Run history for Last updated', 'outcome': 'META'})

    src_block = {'type': 'bigquery', 'project_id': cfg['BIGQUERY']['project_id'], 'dataset': cfg['BIGQUERY']['dataset'], 'table': cfg['BIGQUERY']['table'], 'credentials_file': cfg['BIGQUERY']['credentials_file']} if source == 'bigquery' else {'type': 'csv', 'file': cfg['FEAT_CSV']}
    try:
        import joblib
        cols = joblib.load(cfg['MODELS_DIR'] + 'feature_cols.pkl')
    except Exception:
        cols = []
    contract = {
        'generated_at': now, 'pipeline_version': '2.0',
        'project': {'name': cfg['CLIENT_NAME'], 'domain': cfg['DOMAIN'], 'client_id': cfg['CLIENT_ID'], 'description': cfg['DESCRIPTION']},
        'terminology': cfg['TERMINOLOGY'],
        'outcomes': {
            'understand': {'kpis': 'understand/kpis.json', 'charts': 'understand/charts/', 'segments': 'understand/segments.json', 'anomalies': 'understand/anomalies.json'},
            'decide': {'insights': 'decide/insights.json', 'recommendations': 'decide/recommendations.json', 'simulations': 'decide/simulations/', 'goals': 'decide/goals.json'},
            'monitor': {'forecast': 'monitor/forecast.json', 'goal_progress': 'monitor/goal_progress.json', 'alerts': 'monitor/alerts.json'}},
        'model': {'type': met.get('model_source', 'n/a'), 'pkl_file': 'models/best_classifier.pkl', 'feature_cols_file': 'models/feature_cols.pkl',
                  'input_fields': cols, 'output_label': 'churn_probability_next_month', 'horizon': '1 month',
                  'risk_thresholds': met.get('risk_thresholds'), 'test_metrics': met.get('final_test_metrics')},
        'frontend': {'framework': 'vanilla HTML/JS', 'deploy_target': 'cloudflare_pages'},
        'source': src_block, 'files': files, 'saas_ready': True}
    write_json(contract, O + 'frontend_contract.json')
    kb = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(O) for f in fs) / 1024.0
    print('[export_for_frontend] source:', source, '| files:', len(files) + 1, '| %.1f KB' % kb, '| contract:', O + 'frontend_contract.json')


if __name__ == '__main__':
    main()
