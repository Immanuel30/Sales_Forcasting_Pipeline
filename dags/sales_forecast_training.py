from datetime import datetime, timedelta
from airflow.decorators import dag, task


import pandas as pd
import sys
#inlcude
sys.path.append('/usr/local/airflow/include')
from utils.data_generator import RealisticSalesDataGenerator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 10, 8),
    'catchup': False,
    'schedule': '@weekly',

}

@dag(
    default_args=default_args,
    description='Sales Forecast Training DAG',
    tags=['ml', 'sales', 'forecasting', 'training'],
)

def sales_forecast_training():
    @task()
    def extract_data_task():
        data_outut_dir = 'tmp/sales_data'
        generator = RealisticSalesDataGenerator(
            start_date='2024-01-01',
            end_date='2024-03-31',
        )

        print("Generating reliatic sales data...")
        file_paths = generator.generate_sales_data(output_dir=data_outut_dir)
        for path in file_paths:
            print(f"Generated data file: {path}")


    extract_result = extract_data_task()

sales_forecast_training_dag = sales_forecast_training()

    