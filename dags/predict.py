from airflow.decorators import dag, task
from pendulum import datetime
from astro import sql as aql 
from mlflow_provider.operators.registry import (
    GetLatestModelVersionsOperator,
)

from mlflow_provider.operators.pyfunc import (
    AirflowPredictOperator
)


from astro.sql.table import Table, Metadata

from pandas import DataFrame

QUERY_STATEMENT = """
        SELECT feature_id, sepal_length_cm, sepal_width_cm, petal_length_cm, petal_width_cm
        FROM public.new_features ORDER BY feature_id
    """

@dag(
    start_date=datetime(2022, 1, 1),
    schedule_interval=None,
    default_args={
        'mlflow_conn_id': 'mlflow_astronomer_dev'
    },
    tags=["example"],
    catchup=False,
    render_template_as_native_obj=True
)
def predict():
    """
    ### Sample DAG

    Showcases the sample provider package's operator and sensor.

    To run this example, create an HTTP connection with:
    - id: mlflow_default
    - type: http
    - host: MLflow tracking URI (if MLFlow is hosted on Databricks use your Databricks host)
    """

    @task(multiple_outputs=True)
    def preprocess(result_list: list):
        columns = [
            'feature_id',
            'sepal_length_cm',
            'sepal_width_cm',
            'petal_length_cm',
            'petal_width_cm'
        ]
        df = DataFrame(data=result_list, columns=columns)
        return {'values': df.drop('feature_id', axis=1).values.tolist(), 'ids': df['feature_id'].to_list() }

    preprocessed = preprocess(result_list=aql.get_value_list(sql=QUERY_STATEMENT, conn_id='postgres'))

    latest_staging_model = GetLatestModelVersionsOperator(
        task_id='latest_staging_model',
        name='mlflow_lightgbm_tutorial',
        stages=['Staging']
    )

    prediction = AirflowPredictOperator(
        task_id='prediction',
        model_uri="mlflow-artifacts:/3/{{ ti.xcom_pull(task_ids='latest_staging_model')['model_versions'][0]['run_id'] }}/artifacts/model",
        data="{{ ti.xcom_pull(task_ids='preprocess', key='values') }}"
    )

    output_table = Table(
        name='tmp_predictions',
        conn_id="postgres",
        temp=True
    )

    @aql.dataframe(columns_names_capitalization="lower")
    def post_process(results: list, ids: list):
        final_prediction = []

        for result in results:
            max_index = result.index(max(result))
            final_prediction.append(max_index)
        
        df = DataFrame(data=ids, columns=['feature_id'])
        df['prediction'] = final_prediction
        return df

    classes = post_process(
        results=prediction.output, 
        ids="{{ ti.xcom_pull(task_ids='preprocess', key='ids') }}",
        output_table=output_table
    )

    target_table = Table(
        name='predictions',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres",
    )

    load_predictions = aql.append(
        source_table=output_table,
        target_table=target_table,
        columns=[
            'feature_id',
            'prediction'
        ]
    )

    cleanup = aql.cleanup()
    preprocessed >> latest_staging_model >> prediction >> classes >> load_predictions >> cleanup

predict = predict()
