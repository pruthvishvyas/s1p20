# [NOTE] config/config.py   | OUTCOME: foundation for UNDERSTAND / DECIDE / MONITOR
import os

CONFIG = {
    'CLIENT_ID': 'b2b_saas_revenue',
    'CLIENT_NAME': 'B2B SaaS Revenue and Retention',
    'DOMAIN': 'b2b_saas_subscription',
    'DESCRIPTION': 'Account-month subscription data: predicts churn, protects MRR, flags cash and margin leaks.',
    'OUTCOME_LAYERS': ['UNDERSTAND', 'DECIDE', 'MONITOR'],
    'SAAS_READY': True,
    'TERMINOLOGY': {'revenue': 'MRR', 'customer': 'Account', 'product': 'Plan', 'transaction': 'Invoice'},
    'COLS': {
        'month': 'Month', 'account': 'Account_ID', 'segment': 'Segment', 'region': 'Region', 'industry': 'Industry',
        'channel': 'Channel', 'plan': 'Plan', 'contract': 'Contract_Type', 'cohort': 'Cohort_Month',
        'tenure': 'Tenure_Months', 'seats': 'Seats', 'list_price': 'List_Price_Per_Seat', 'discount': 'Discount_Pct',
        'net_price': 'Net_Price_Per_Seat', 'mrr_start': 'Starting_MRR', 'mrr_new': 'New_MRR',
        'mrr_exp': 'Expansion_MRR', 'mrr_con': 'Contraction_MRR', 'mrr_churn': 'Churned_MRR', 'mrr_end': 'Ending_MRR',
        'revenue': 'Revenue', 'hosting': 'Hosting_Cost', 'support_cost': 'Support_Cost',
        'cs_cost': 'Customer_Success_Cost', 'pay_fees': 'Payment_Fees', 'cogs': 'COGS', 'gross_profit': 'Gross_Profit',
        'cac': 'CAC_Allocated', 'contrib': 'Contribution_Profit', 'terms': 'Terms_Days', 'invoiced': 'Invoiced',
        'cash': 'Cash_Collected', 'bad_debt': 'Bad_Debt_Writeoff', 'ar_open': 'AR_Opening', 'ar_close': 'AR_Closing',
        'ar60': 'AR_60Plus', 'cash_contrib': 'Cash_Contribution', 'health': 'Health_Score',
        'active_users': 'Active_Users', 'logins': 'Logins', 'tickets': 'Support_Tickets', 'new_logo': 'New_Logo_Flag',
        'first_row': 'First_Row_Flag', 'churn': 'Churn_Flag', 'churn_reason': 'Churn_Reason',
    },
    'CAT_KEYS': ['segment', 'region', 'industry', 'channel', 'plan', 'contract'],
    'NONNEG_KEYS': ['seats', 'list_price', 'net_price', 'mrr_start', 'mrr_new', 'mrr_exp', 'mrr_con', 'mrr_churn',
                    'mrr_end', 'revenue', 'hosting', 'support_cost', 'cs_cost', 'pay_fees', 'cogs', 'cac', 'invoiced',
                    'cash', 'bad_debt', 'ar_open', 'ar_close', 'ar60', 'active_users', 'logins', 'tickets', 'tenure'],
    # usage/cost spikes are capped at the 99.5th percentile; money flows are never capped (large accounts are real)
    'CAP_KEYS': ['logins', 'tickets', 'hosting', 'support_cost'],
    'CAP_QUANTILE': 0.995,
    'CONTRACT_TERM_MONTHS': {'Monthly': 1, 'Quarterly': 3, 'Semi-Annual': 6, 'Annual': 12, 'Biennial': 24, 'Multi-Year': 36},
    # ---- modelling
    'RANDOM_STATE': 42,
    'TEST_MONTH_FRAC': 0.2,
    'MIN_ROWS': 500, 'MIN_ACCOUNTS': 30, 'MIN_MONTHS': 6,
    'MIN_POS_TOTAL': 40, 'MIN_POS_TRAIN': 25, 'MIN_POS_TEST': 8,
    'MIN_ACCOUNTS_SEG': 40, 'MIN_MONTHS_FORECAST': 12,
    'ANOMALY_CONT': 0.02,           # review ~2% of account-months: a CS team can triage this many
    'RISK_HIGH_QUANTILE': 0.90, 'RISK_MED_QUANTILE': 0.70,
    'MODEL_NUM_KEYS': ['tenure', 'seats', 'discount', 'net_price', 'health', 'active_users', 'logins', 'tickets', 'terms'],
    'MODEL_CAT_KEYS': ['segment', 'region', 'industry', 'channel', 'plan', 'contract'],
    'MODEL_ENG_FEATURES': ['seat_utilization', 'logins_per_active_user', 'logins_per_seat', 'gross_margin_pct',
                           'contribution_margin_pct', 'contrib_margin_3m', 'cost_to_serve_ratio', 'support_cost_ratio',
                           'tickets_per_seat', 'price_realization', 'heavy_discount_flag', 'collection_rate_3m',
                           'ar_days', 'ar60_ratio', 'overdue_flag', 'term_months', 'tenure_mod_term',
                           'months_to_renewal', 'renewal_within_3m', 'is_monthly', 'health_change_1m', 'health_roll3',
                           'health_drop_flag', 'active_users_change_1m', 'logins_change_3m', 'tickets_roll3',
                           'mrr_growth_3m', 'expansion_6m', 'contraction_6m', 'is_first_year', 'log_mrr', 'log_seats'],
    'SEG_RAW': ['health', 'discount', 'tenure'],
    'SEG_ENG': ['log_mrr', 'seat_utilization', 'contrib_margin_3m', 'tickets_roll3'],
    'ANOM_FEATURES': ['health_change_1m', 'logins_change_3m', 'active_users_change_1m', 'mrr_growth_3m',
                      'tickets_roll3', 'cost_to_serve_ratio', 'ar_days'],
    # ---- domain thresholds (B2B SaaS benchmarks)
    'THRESHOLDS': {
        'health_red': 50,              # customer-success health scores below 50 are conventionally "red"
        'health_green': 75,
        'utilization_low': 0.40,       # <40% of paid seats active: shelfware, top churn predictor in seat-based SaaS
        'utilization_high': 0.85,      # >85% seats active: little headroom, natural upsell trigger
        'gross_margin_floor': 0.70,    # 70% is the lower bound of healthy SaaS gross margin
        'discount_cap': 0.30,          # >30% off list erodes price realisation
        'support_cost_ratio_max': 0.10,
        'ar_days_multiple': 2.0,       # collections issue when AR outstanding > 2x contractual terms
        'renewal_window_months': 3,    # CS needs ~90 days to run a renewal motion
        'low_util_for_rule': 0.40,
    },
    'SIM': {
        'price_churn_sensitivity': 1.5,     # ASSUMPTION: +10% price -> +15% relative churn probability (client can tune)
        'campaign_cost_months_of_cs': 3.0,  # retention play costs ~3 months of average CS effort per account
        'campaign_save_rates': [0.10, 0.20, 0.30],
        'campaign_top_pcts': [0.05, 0.10, 0.15, 0.20, 0.30],
        'value_horizon_months': 12,
        'expansion_uplift_pct': 0.15,       # ASSUMPTION: upsell lifts MRR 15% on expansion-ready accounts
    },
    'FORECAST_HORIZON_MONTHS': 6, 'FORECAST_WINDOW': 6,
    'BIGQUERY': {'project_id': '', 'dataset': '', 'table': 'feat', 'credentials_file': 'credentials.json'},
}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ROOT = BASE_DIR.replace('\\', '/')
if not ROOT.endswith('/'):
    ROOT += '/'

__RAW__ = 's1p20.csv'.replace('\\', '/')
RAW_CSV_CANDIDATES = [
    os.path.join(ROOT, 'raw', __RAW__),
    os.path.join(ROOT, 'data', 'raw', __RAW__),
    os.path.join(ROOT, 'raw', '*.csv'),
    os.path.join(ROOT, 'data', 'raw', '*.csv'),
    os.path.abspath(os.path.join('.', 'raw', __RAW__)),
    os.path.abspath(os.path.join('.', 'data', 'raw', __RAW__)),
]

RAW_CSV = next((p for p in RAW_CSV_CANDIDATES if os.path.exists(p)), os.path.join(ROOT, 'raw', __RAW__))

CONFIG.update({
    'ROOT': ROOT,
    'RAW_CSV': RAW_CSV,
    'PROCESSED_CSV': ROOT + 'data/processed/clean_data.csv',
    'FEAT_CSV': ROOT + 'data/processed/feature_store.csv',
    'VALIDATION_JSON': ROOT + 'data/processed/validation_report.json',
    'ML1_CSV': ROOT + 'data/processed/ml_task1_output.csv',
    'ML2_CSV': ROOT + 'data/processed/ml_task2_output.csv',
    'SEGMENTS_CSV': ROOT + 'data/processed/segments.csv',
    'BIZ_CSV': ROOT + 'data/processed/business_logic_output.csv',
    'FORECAST_CSV': ROOT + 'data/processed/forecast_output.csv',
    'SIM_DIR': ROOT + 'data/processed/simulations/',
    'GOALS_JSON': ROOT + 'config/goals.json',
    'REPORTS_DIR': ROOT + 'reports/',
    'MODELS_DIR': ROOT + 'models/',
    'OUTPUT_DIR': ROOT + 'output/',
    'INSIGHTS_JSON': ROOT + 'reports/insights.json',
    'METRICS_JSON': ROOT + 'models/classifier_metrics.json',
    'IMPORTANCE_JSON': ROOT + 'models/feature_importance.json',
    'FORECAST_MODEL': ROOT + 'models/forecast_model.pkl',
})

for _d in ['data/raw/', 'data/processed/', 'data/processed/simulations/', 'config/', 'reports/', 'models/', 'output/']:
    os.makedirs(ROOT + _d, exist_ok=True)

print('CONFIG ready for client:', CONFIG['CLIENT_ID'])
