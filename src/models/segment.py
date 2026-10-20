# [NOTE] src/models/segment.py   | OUTCOME: UNDERSTAND (segments + anomalies)
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from src.utils import save_fig


def _name_clusters(prof, c):
    z = (prof - prof.mean()) / prof.std(ddof=0).replace(0, 1)
    z = z.fillna(0)
    h, u = c['health'], 'seat_utilization'
    rules = [('Champions', lambda r: r[h] + r[u] + r['log_mrr']),
             ('At-Risk / Low Health', lambda r: -r[h] - r['tickets_roll3']),
             ('Under-Adopting', lambda r: -r[u]),
             ('Heavily Discounted', lambda r: r[c['discount']])]
    names, left = {}, list(z.index)
    for label, fn in rules:
        if not left:
            break
        best = max(left, key=lambda k: fn(z.loc[k]))
        names[best] = label
        left.remove(best)
    for i, k in enumerate(left):
        names[k] = 'Core Stable' + ('' if i == 0 else ' ' + chr(66 + i - 1))
    return names


def run_segmentation(df, config):
    c, rs = config['COLS'], config['RANDOM_STATE']
    df = df.copy()
    snap = df[(df['is_latest_month'] == 1) & (df[c['churn']] == 0)].copy()
    feats = [c[k] for k in config['SEG_RAW']] + config['SEG_ENG']
    df['segment_name'] = 'Unsegmented'
    if len(snap) < config['MIN_ACCOUNTS_SEG']:
        print('[segment] WARNING: only', len(snap), 'active accounts; segmentation skipped (fallback label Unsegmented)')
    else:
        Xs = StandardScaler().fit_transform(snap[feats].fillna(0)).clip(-3, 3)
        best_k, best_s = 3, -1.0
        for k in range(3, min(6, len(snap) // 10) + 1):
            lab = KMeans(n_clusters=k, n_init=10, random_state=rs).fit_predict(Xs)
            s = silhouette_score(Xs, lab, sample_size=min(4000, len(Xs)), random_state=rs)
            if s > best_s:
                best_k, best_s = k, float(s)
        km = KMeans(n_clusters=best_k, n_init=10, random_state=rs).fit(Xs)
        snap['cluster'] = km.labels_
        names = _name_clusters(snap.groupby('cluster')[feats].mean(), c)
        snap['segment_name'] = snap['cluster'].map(names)
        df['segment_name'] = df[c['account']].map(dict(zip(snap[c['account']], snap['segment_name']))).fillna('Unsegmented')
        keep = [c['account'], c['segment'], c['plan'], c['mrr_end'], 'segment_name'] + feats
        snap[keep].to_csv(config['SEGMENTS_CSV'], index=False, encoding='utf-8')
        joblib.dump({'kmeans': km, 'features': feats, 'names': names, 'silhouette': best_s}, config['MODELS_DIR'] + 'segmentation.pkl')
        print('[segment] k=%d silhouette=%.3f' % (best_k, best_s))
        print(snap.groupby('segment_name').agg(accounts=(c['account'], 'count'), mrr=(c['mrr_end'], 'sum')).round(0))
        pc = PCA(n_components=2, random_state=rs).fit_transform(Xs)
        fig, ax = plt.subplots(figsize=(7, 5))
        for nm in sorted(snap['segment_name'].unique()):
            m = (snap['segment_name'] == nm).to_numpy()
            ax.scatter(pc[m, 0], pc[m, 1], s=12, alpha=0.6, label=nm)
        ax.legend(fontsize=8); ax.set_title('Account segments (PCA view)')
        save_fig(fig, config['REPORTS_DIR'] + 'ml2_segments.png')

    # anomaly detection on active account-months: unusual movement in health, usage, revenue, cost or cash
    af = [f for f in config['ANOM_FEATURES'] if f in df.columns]
    act = df[df[c['churn']] == 0]
    df['is_anomaly'], df['anomaly_score'], df['anomaly_driver'] = 0, np.nan, ''
    if len(act) >= 200 and af:
        Xa = act[af].fillna(0)
        iso = IsolationForest(n_estimators=200, contamination=config['ANOMALY_CONT'], random_state=rs, n_jobs=-1).fit(Xa)
        med = Xa.median()
        mad = (Xa - med).abs().median() * 1.4826
        sd = Xa.std().replace(0, 1)
        scale = mad.where(mad > 0, sd).replace(0, 1)
        z = (Xa - med) / scale
        driver = z.abs().idxmax(axis=1)
        zval = z.abs().max(axis=1)
        df.loc[act.index, 'is_anomaly'] = (iso.predict(Xa) == -1).astype(int)
        df.loc[act.index, 'anomaly_score'] = -iso.score_samples(Xa)
        df.loc[act.index, 'anomaly_driver'] = driver.astype(str) + ' (z=' + zval.round(1).astype(str) + ')'
        joblib.dump(iso, config['MODELS_DIR'] + 'isolation_forest.pkl')
    else:
        print('[segment] WARNING: not enough active rows for anomaly detection; skipped')
    an = df[df['is_anomaly'] == 1][[c['account'], c['month'], 'anomaly_score', 'anomaly_driver', c['mrr_end'], c['health']]]
    an.sort_values('anomaly_score', ascending=False).to_csv(config['ML2_CSV'], index=False, encoding='utf-8')
    print('[segment] anomalies flagged:', len(an), '->', config['ML2_CSV'])
    return df
