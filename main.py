# [NOTE] main.py
import sys
from config.config import CONFIG
from src.data.ingest import load_and_validate
from src.data.clean import clean
from src.features.engineer import engineer
from src.analytics.eda import run_eda
from src.models.classify import run_classification
from src.models.segment import run_segmentation
from src.models.forecast import run_forecast
from src.analytics.business import run_business_logic
from src.analytics.insights import run_insights
from src.reporting.export import export


def main():
    phases = [
        ('Ingestion', lambda df: load_and_validate(CONFIG), True),
        ('Cleaning', lambda df: clean(df, CONFIG), True),
        ('Engineering', lambda df: engineer(df, CONFIG), True),
        ('EDA', lambda df: run_eda(df, CONFIG) or df, False),
        ('Churn model', lambda df: run_classification(df, CONFIG), True),
        ('Segments and anomalies', lambda df: run_segmentation(df, CONFIG), False),
        ('Forecast', lambda df: run_forecast(df, CONFIG) and df, False),
        ('Business logic', lambda df: run_business_logic(df, CONFIG), True),
        ('Insights', lambda df: run_insights(df, CONFIG) or df, False),
        ('Export', lambda df: export(df, CONFIG) or df, False),
    ]
    df = None
    for name, fn, critical in phases:
        try:
            print('Phase:', name)
            result = fn(df)
            if result is not None and hasattr(result, 'shape'):
                df = result
        except Exception as e:
            print('Phase', name, 'FAILED:', repr(e))
            if critical:
                sys.exit(1)
    print('Pipeline complete. Next: python export_for_frontend.py')


if __name__ == '__main__':
    main()
