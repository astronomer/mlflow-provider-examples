"""
### Feature Engineering Pipeline to use with MLflow provider example DAGs.

Generates synthetic data and performs feature engineering.
"""

from pendulum import datetime
import logging

from airflow.decorators import dag
from astro import sql as aql 
from astro.sql.table import Table, Metadata
from airflow import Dataset

from pandas import DataFrame

experiment_name = 'mlflow_lightgbm_tutorial'

test_sample = {
    'data':[
        [5.1, 3.5, 1.4, 0.2],
        [4.9, 3. , 1.4, 0.2],
        [4.7, 3.2, 1.3, 0.2],
    ],
    'columns': [
        'sepal_length_cm',
        'sepal_width_cm',
        'petal_length_cm',
        'petal_width_cm'
    ]
}

@dag(
    start_date=datetime(2022, 1, 1),
    schedule_interval=None,
    tags=["example"],
    default_view="graph",
    catchup=False,
    doc_md=__doc__
)
def feature_eng():

    @aql.transform
    def get_data(input_table: Table): 
        return """ 
            SELECT 
                sepal_length_cm,
                sepal_width_cm,
                petal_length_cm,
                petal_width_cm
            FROM {{input_table}}
        """ 
    
    @aql.dataframe(columns_names_capitalization="lower")
    def generate_features(
        df: DataFrame,
        num_new_records: int,
        max_increase_limit: float = 0.0,
        min_decrease_limit: float = 0.0,
    ):
        import random

        max_values = []
        for col in df.columns:
            max_value = df.describe()[col]['max']
            max_values.append(max_value)
        logging.info(f"Max values for each column: {max_values}")
            
        min_values = []
        for col in df.columns:
            min_value = df.describe()[col]['min']
            min_values.append(min_value)
        logging.info(f"Min values for each column: {min_values}")
        
        increase_max_by = 0
        if max_increase_limit > 0:
            increase_max_by = [random.uniform(x, x+max_increase_limit) for x in max_values]
        logging.info(f"Randomly increase max by: {increase_max_by}")
        
        decrease_min_by = 0
        if min_decrease_limit > 0:
            decrease_min_by = [random.uniform(x-min_decrease_limit, x) for x in  min_values]
        logging.info(f"Randomly decrease min by: {decrease_min_by}")
        
        synthetic_records = []
        for i in range(num_new_records):
            record = []
            for j in range(4):
                new_value = round(random.uniform(decrease_min_by[j], increase_max_by[j]),1)
                if new_value < 0:
                    new_value = 0.11
                record.append(new_value)
            synthetic_records.append(record)
        
        synthetic_records = DataFrame(data=synthetic_records, columns=df.columns)
        return synthetic_records

    input_table = Table(
        name='iris_ground_truth',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres"
    )

    output_table = Table(
        name='temp_new_features',
        conn_id="postgres",
        temp=True
    )

    target_table = Table(
        name='new_features',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres",
    )

    original_data = get_data(input_table)

    features = generate_features(
        df=original_data,
        num_new_records=5,
        max_increase_limit=2.0,
        min_decrease_limit=0.1,
        output_table=output_table,
    )

    load_features = aql.append(
        source_table=features,
        target_table=target_table,
        columns=[
            'sepal_length_cm',
            'sepal_width_cm',
            'petal_length_cm',
            'petal_width_cm'
        ]
    )

    cleanup = aql.cleanup()

    load_features >> cleanup

feature_eng = feature_eng()
