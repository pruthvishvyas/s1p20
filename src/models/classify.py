# [NOTE] src/models/classify.py   | OUTCOME: UNDERSTAND + DECIDE (next-month churn risk per account)
import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedGroupKFold, GroupShuffleSplit, cross_val_score
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, roc_curve, precision_recall_curve
from sklearn.inspection import permutation_importance
from src.utils import write_json, save_fig


def build_matrix(df, config, columns=None):
    c = config['COLS']
    num = [c[k] for k in config['MODEL_NUM_KEYS']] + config['MODEL_ENG_FEATURES']
    cat = [c[k] for k in config['MODEL_CAT_KEYS']]
    num = [x for x in num if x in df.columns]
    cat = [x for x in cat if x in df.columns]
    X = pd.concat([df[num].apply(pd.to_numeric, errors='coerce'), pd.get_dummies(df[cat].astype(str), dtype=float)], axis=1)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X.replace([np.inf, -np.inf], np.nan)


def rule_score(df, config):
    c, t = config['COLS'], config['THRESHOLDS']
    s = 2.0 * (df[c['health']] < t['health_red']) + 1.0 * (df['seat_utilization'] < t['utilization_low'])
    s = s + 2.0 * df['renewal_within_3m'] + 1.0 * df['health_drop_flag'] + 1.0 * df['overdue_flag']
    return s.astype(float)


def _metrics(y, p):
    y, p = np.asarray(y).astype(int), np.asarray(p, dtype=float)
    out = {'n': int(len(y)), 'positives': int(y.sum())}
    if y.sum() == 0 or y.sum() == len(y):
        return out
    k = max(1, int(len(y) * 0.10))
    top = np.argsort(-p)[:k]
    out.update({'roc_auc': float(roc_auc_score(y, p)), 'pr_auc': float(average_precision_score(y, p)),
                'brier': float(brier_score_loss(y, np.clip(p, 0, 1))),
                'recall_top10pct': float(y[top].sum() / y.sum()), 'lift_top10pct': float(y[top].mean() / y.mean())})
    return out


def run_classification(df, config):
    c, rs = config['COLS'], config['RANDOM_STATE']
    df = df.copy()
    X_all = build_matrix(df, config)
    cols = list(X_all.columns)
    lab_mask = (df['label_valid'] == 1)
    y_all = df['churn_next_month']
    base_rate = float(y_all[lab_mask].mean()) if lab_mask.sum() else 0.0
    n_pos = int(y_all[lab_mask].sum()) if lab_mask.sum() else 0
    active = (df[c['churn']] == 0)
    meta = {'target': 'churn_next_month', 'population': 'active accounts with a next-month observation',
            'labeled_rows': int(lab_mask.sum()), 'positives': n_pos, 'base_rate': base_rate, 'feature_count': len(cols)}
    df['model_split'] = 'other'
    df.loc[df['is_latest_month'] == 1, 'model_split'] = 'latest'

    if n_pos < config['MIN_POS_TOTAL']:
        print('[classify] WARNING: only', n_pos, 'churn events (<', config['MIN_POS_TOTAL'], '). Using rule-based fallback, no ML claims.')
        rs_ = rule_score(df, config)
        df['churn_prob'] = np.where(active, (rs_ / max(rs_.max(), 1.0)) * 0.5, np.nan)
        meta.update({'model_source': 'rule_based_fallback', 'ml_valid': False})
        final, thr = None, None
    else:
        months = sorted(df.loc[lab_mask, config['COLS']['month']].unique())
        n_test = max(3, int(round(len(months) * config['TEST_MONTH_FRAC'])))
        test_m, train_m = months[-n_test:], months[:-(n_test + 1)]
        mcol = df[c['month']]
        tr_idx = df.index[lab_mask & mcol.isin(train_m)]
        te_idx = df.index[lab_mask & mcol.isin(test_m)]
        split_mode = 'time_split_with_1_month_purge'
        ok = len(tr_idx) > 0 and len(te_idx) > 0 and y_all[tr_idx].sum() >= config['MIN_POS_TRAIN'] and y_all[te_idx].sum() >= config['MIN_POS_TEST']
        if not ok:
            print('[classify] time split lacks positives -> falling back to account-grouped random split')
            gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=rs)
            li = df.index[lab_mask].to_numpy()
            a, b = next(gss.split(li, groups=df.loc[li, c['account']]))
            tr_idx, te_idx = li[a], li[b]
            split_mode = 'grouped_random_split'
        df.loc[tr_idx, 'model_split'] = 'train'
        df.loc[te_idx, 'model_split'] = 'test'
        Xtr, ytr, gtr = X_all.loc[tr_idx], y_all[tr_idx].astype(int), df.loc[tr_idx, c['account']]
        Xte, yte = X_all.loc[te_idx], y_all[te_idx].astype(int)
        print('[classify] split:', split_mode, '| train rows', len(tr_idx), 'pos', int(ytr.sum()), '| test rows', len(te_idx), 'pos', int(yte.sum()))
        base = _metrics(yte, rule_score(df.loc[te_idx], config).values)
        print('[classify] rule baseline  PR-AUC %.3f  ROC-AUC %.3f  recall@top10%% %.3f' % (base.get('pr_auc', 0), base.get('roc_auc', 0), base.get('recall_top10pct', 0)))
        imp = ('imp', SimpleImputer(strategy='median'))
        models = {
            'LogisticRegression': Pipeline([imp, ('sc', StandardScaler()), ('clf', LogisticRegression(max_iter=3000, C=0.5, class_weight='balanced'))]),
            'RandomForest': Pipeline([imp, ('clf', RandomForestClassifier(n_estimators=300, min_samples_leaf=10, max_features='sqrt', class_weight='balanced_subsample', n_jobs=-1, random_state=rs))]),
            'HistGradientBoosting': HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=250, l2_regularization=1.0, min_samples_leaf=30, class_weight='balanced', random_state=rs),
        }
        cv = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=rs)
        results = {}
        for name, mdl in models.items():
            try:
                cvs = cross_val_score(mdl, Xtr, ytr, cv=cv, groups=gtr, scoring='average_precision')
                cv_m, cv_s = float(cvs.mean()), float(cvs.std())
            except Exception as e:
                print('[classify] CV skipped for', name, ':', e); cv_m, cv_s = float('nan'), float('nan')
            mdl.fit(Xtr, ytr)
            met = _metrics(yte, mdl.predict_proba(Xte)[:, 1])
            met.update({'cv_pr_auc_mean': cv_m, 'cv_pr_auc_std': cv_s})
            results[name] = met
            print('[classify] %-22s CV PR-AUC %.3f+-%.3f | test PR-AUC %.3f ROC-AUC %.3f recall@10%% %.3f lift@10%% %.2f' % (
                name, cv_m, cv_s, met.get('pr_auc', 0), met.get('roc_auc', 0), met.get('recall_top10pct', 0), met.get('lift_top10pct', 0)))
        best = max(results, key=lambda k: results[k].get('pr_auc', -1))
        print('[classify] best model on held-out data:', best)
        # calibrate so probabilities can be multiplied by MRR to estimate dollars at risk
        eval_model = models[best]
        method = 'isotonic' if int(ytr.sum()) >= 200 else 'sigmoid'
        try:
            splits = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=rs).split(Xtr, ytr, gtr))
            cal = CalibratedClassifierCV(estimator=clone(models[best]), method=method, cv=splits).fit(Xtr, ytr)
            cal_met = _metrics(yte, cal.predict_proba(Xte)[:, 1])
            if cal_met.get('brier', 9) <= results[best].get('brier', 9):
                eval_model, results[best + '_calibrated'] = cal, cal_met
                print('[classify] calibration (%s) improved Brier %.4f -> %.4f' % (method, results[best]['brier'], cal_met['brier']))
        except Exception as e:
            print('[classify] calibration skipped:', e)
        final_met = _metrics(yte, eval_model.predict_proba(Xte)[:, 1])
        # refit the chosen recipe on ALL labeled rows for production scoring
        lab_idx = df.index[lab_mask]
        final = clone(eval_model).fit(X_all.loc[lab_idx], y_all[lab_idx].astype(int))
        p_all = final.predict_proba(X_all)[:, 1]
        df['churn_prob'] = np.where(active, p_all, np.nan)
        meta.update({'model_source': best + ('+calibrated' if eval_model is not models[best] else ''), 'ml_valid': True,
                     'split_mode': split_mode, 'baseline_rule': base, 'models': results, 'final_test_metrics': final_met})
        # plots on the held-out set
        pe = eval_model.predict_proba(Xte)[:, 1]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
        fpr, tpr, _ = roc_curve(yte, pe); ax[0].plot(fpr, tpr, color='#264653'); ax[0].plot([0, 1], [0, 1], '--', color='grey')
        ax[0].set_title('ROC (held-out months) AUC=%.3f' % final_met.get('roc_auc', 0)); ax[0].set_xlabel('FPR'); ax[0].set_ylabel('TPR')
        pr, rc, _ = precision_recall_curve(yte, pe); ax[1].plot(rc, pr, color='#e76f51'); ax[1].axhline(float(yte.mean()), ls='--', color='grey')
        ax[1].set_title('Precision-Recall PR-AUC=%.3f' % final_met.get('pr_auc', 0)); ax[1].set_xlabel('Recall'); ax[1].set_ylabel('Precision')
        save_fig(fig, config['REPORTS_DIR'] + 'ml1_roc_pr.png')
        try:
            sample = Xte.sample(min(3000, len(Xte)), random_state=rs)
            pi = permutation_importance(eval_model, sample, yte.loc[sample.index], n_repeats=3, random_state=rs, scoring='average_precision', n_jobs=1)
            imp_s = pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False)
            write_json({'method': 'permutation_importance_pr_auc', 'features': [{'feature': k, 'importance': float(v)} for k, v in imp_s.head(20).items()]}, config['IMPORTANCE_JSON'])
            top = imp_s.head(15)[::-1]
            fig, ax = plt.subplots(figsize=(8, 5.5)); ax.barh(top.index, top.values, color='#2a9d8f'); ax.set_title('Top drivers of next-month churn (permutation importance)')
            save_fig(fig, config['REPORTS_DIR'] + 'ml1_feature_importance.png')
        except Exception as e:
            print('[classify] importance skipped:', e)
        joblib.dump(final, config['MODELS_DIR'] + 'best_classifier.pkl')
        joblib.dump(cols, config['MODELS_DIR'] + 'feature_cols.pkl')
        print('[classify] saved best_classifier.pkl and feature_cols.pkl')

    sc = df.loc[active & df['churn_prob'].notna(), 'churn_prob']
    hi = max(float(sc.quantile(config['RISK_HIGH_QUANTILE'])), 2 * base_rate) if len(sc) else 1.0
    md = min(max(float(sc.quantile(config['RISK_MED_QUANTILE'])), base_rate), hi) if len(sc) else 1.0
    df['risk_level'] = np.where(df['churn_prob'].isnull(), None, np.where(df['churn_prob'] >= hi, 'HIGH', np.where(df['churn_prob'] >= md, 'MEDIUM', 'LOW')))
    meta['risk_thresholds'] = {'high': hi, 'medium': md}
    write_json(meta, config['METRICS_JSON'])
    out = df.loc[df['churn_prob'].notna(), [c['account'], c['month'], 'churn_prob', 'risk_level', 'model_split', 'churn_next_month']]
    out.to_csv(config['ML1_CSV'], index=False, encoding='utf-8')
    print('[classify] risk thresholds high>=%.3f medium>=%.3f | scored rows %d -> %s' % (hi, md, len(out), config['ML1_CSV']))
    return df
