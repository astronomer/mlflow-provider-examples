"""
### Generate True Values with MLflow

Artificially generates feedback on the predictions made by the model in the predict DAG.
"""

from pendulum import datetime

from airflow.decorators import dag
from astro import sql as aql
from astro.sql.table import Table, Metadata

from pandas import DataFrame

@dag(
    start_date=datetime(2022, 1, 1),
    schedule=None,
    tags=["example"],
    default_view="grid",
    catchup=False,
    doc_md=__doc__
)
def generate_true_values():

    @aql.transform
    def get_data(input_table: Table):
        return """
            SELECT
                feature_id,
                prediction
            FROM {{input_table}}
        """

    @aql.dataframe(columns_names_capitalization="lower")
    def generate_true_values(predictions: DataFrame):
        import random

        predicted_values = predictions['prediction'].to_list()

        feedback=[]
        for p in predicted_values:
            x = random.random()
            if x > .9:
                feedback.append(random.randint(0, 2))
            else:
                feedback.append(p)

        true_values = DataFrame(data=predictions['feature_id'].to_list(), columns=['feature_id'])
        true_values['true_values'] = feedback
        return true_values

    input_table = Table(
        name='predictions',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres"
    )

    target_table = Table(
        name='true_values',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres",
    )

    prediction_data = get_data(input_table)

    true_values = generate_true_values(
        predictions=prediction_data,
        output_table=target_table
    )

    cleanup = aql.cleanup()

    true_values >> cleanup

generate_true_values = generate_true_values()
