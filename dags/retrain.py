"""
### Retrain DAG that uses the MLflow provider to track and regiser models

Uses the MLflow provider package's CreateRegisteredModelOperator, CreateModelVersionOperator, and TransitionModelVersionStageOperator to create a new model version in the MLflow model registry and transition it to the "Staging" stage.
"""
from airflow.utils.helpers import chain
from pendulum import datetime

from airflow.decorators import dag, task
from airflow.utils.edgemodifier import Label
from airflow.providers.slack.operators.slack import SlackAPIPostOperator
from astro import sql as aql 
from astro.sql.table import Table, Metadata

from mlflow_provider.hooks.base import MLflowBaseHook
from mlflow_provider.operators.registry import (
    CreateRegisteredModelOperator,
    CreateModelVersionOperator,
    TransitionModelVersionStageOperator
)

from mlflow_provider.operators.deployment import (
    CreateDeploymentOperator,
    PredictOperator
)

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
    default_args={
        # "retries": 2
        'mlflow_conn_id': 'mlflow_default'
    },
    tags=["example"],
    default_view="graph",
    catchup=False,
    doc_md=__doc__
    # render_template_as_native_obj=True
)
def retrain():
    """
    ### Sample DAG

    Showcases the sample provider package's operator and sensor.

    To run this example, create an HTTP connection with:
    - id: mlflow_default
    - type: http
    - host: MLflow tracking URI (if MLFlow is hosted on Databricks use your Databricks host)
    """

    original_table = Table(
        name='iris_ground_truth',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres"
    )

    true_value_table = Table(
        name='true_values',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres",
    )

    new_features_table = Table(
        name='new_features',
        metadata=Metadata(
            schema='public',
            database='feature_store',
        ),
        conn_id="postgres",
    )
    
    @aql.transform
    def get_data(truth_table: Table, new_features_table: Table, original_table: Table): 
        return """ 
            SELECT
                sepal_length_cm,
                sepal_width_cm,
                petal_length_cm,
                petal_width_cm,
                true_values as target
            FROM {{new_features_table}}
            JOIN {{truth_table}}
            ON {{new_features_table}}.feature_id={{truth_table}}.feature_id
            UNION 
            SELECT
                sepal_length_cm,
                sepal_width_cm,
                petal_length_cm,
                petal_width_cm,
                target
            FROM {{original_table}}
        """

    @aql.dataframe(columns_names_capitalization='original')
    def retrain(iris: DataFrame) -> dict[str, str]:
        from sklearn import datasets
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, log_loss
        import lightgbm as lgb
        import matplotlib as mpl

        import mlflow
        import mlflow.lightgbm

        mlflow_hook = MLflowBaseHook(mlflow_conn_id='mlflow_astronomer_dev')
        mlflow_hook._set_env_variables()

        # Creating an experiment and continue if it already exists
        try:
            mlflow.create_experiment(experiment_name)
        except:
            pass
        
        # Setting the environment with the created experiment
        experiment = mlflow.set_experiment(experiment_name)

        X = iris.drop('target', axis=1)
        y = iris['target']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # enable auto logging
        mlflow.lightgbm.autolog()

        train_set = lgb.Dataset(X_train, label=y_train)

        with mlflow.start_run():
            # train model
            params = {
                "objective": "multiclass",
                "num_class": 3,
                # "learning_rate": args.learning_rate,
                "learning_rate": 0.1,
                "metric": "multi_logloss",
                # "colsample_bytree": args.colsample_bytree,
                "colsample_bytree": 1.0,
                # "subsample": args.subsample,
                "subsample": 1.0,
                "seed": 42,
            }
            model = lgb.train(
                params, train_set, num_boost_round=10, valid_sets=[train_set], valid_names=["train"]
            )

            # evaluate model
            y_proba = model.predict(X_test)
            y_pred = y_proba.argmax(axis=1)
            loss = log_loss(y_test, y_proba)
            acc = accuracy_score(y_test, y_pred)

            # log metrics
            metrics = {"log_loss": loss, "accuracy": acc}
            mlflow.log_metrics(metrics)

            run_id = mlflow.active_run().info.run_id
            artifact_location = mlflow.get_experiment(experiment.experiment_id).artifact_location

            return {'experiment_id': experiment.experiment_id, 'run_id': run_id, 'artifact_location': artifact_location, 'metrics': metrics }

    retrain_info = retrain(get_data(true_value_table, new_features_table, original_table))

    send_alert = SlackAPIPostOperator(
        slack_conn_id='slack_default',
        task_id="send_alert",
        text="Warning: Model accuracy has dropped to {{ ti.xcom_pull(task_ids='retrain')['metrics']['accuracy'] }}",
        channel="#integrations"
    )

    @task.branch
    def choose_branch(result):
        if float(result) > 0.90:
            return ['create_registered_model']
        return ['send_alert']

    branch_choice = choose_branch(result="{{ ti.xcom_pull(task_ids='retrain')['metrics']['accuracy'] }}")
    # branch_choice = choose_branch("0.8")

    create_registered_model = CreateRegisteredModelOperator(
        task_id='create_registered_model',
        name=experiment_name,
        tags=[{'key': 'name1', 'value': 'value1'}, {'key': 'name2', 'value': 'value2'}],
        description='ML Ops Offsite Demo'
    )
    create_registered_model.doc_md = 'This task is just in case for a first run and to make sure there is always a registry to add model version to.'

    create_model_version = CreateModelVersionOperator(
        task_id='create_model_version',
        name=experiment_name,
        source=f"{retrain_info['artifact_location']}/model",
        run_id=retrain_info['run_id'],
        trigger_rule='none_skipped'
    )

    transition_model = TransitionModelVersionStageOperator(
        task_id='transition_model',
        name=experiment_name,
        version="{{ ti.xcom_pull(task_ids='create_model_version')['model_version']['version'] }}",
        stage='Staging',
        archive_existing_versions=True
    )

    create_deployment = CreateDeploymentOperator(
        task_id='create_deployment',
        name="mlops-offsite-deployment-{{ ds_nodash }}",
        model_uri="{{ ti.xcom_pull(task_ids='transition_model')['model_version']['source'] }}",
        target_uri='sagemaker:/us-east-2',
        target_conn_id='aws_default',
        config={
            'image_url': "{{ var.value.mlflow_pyfunc_image_url }}",
            'execution_role_arn': "{{ var.value.sagemaker_execution_arn }}"
        },
        flavor='python_function'
    )

    test_prediction = PredictOperator(
        task_id='test_prediction',
        target_uri='sagemaker:/us-east-2',
        target_conn_id='aws_default',
        deployment_name="{{ ti.xcom_pull(task_ids='create_deployment')['name'] }}",
        inputs=DataFrame(data=test_sample['data'], columns=test_sample['columns'])
    )

    chain(create_registered_model, create_model_version, transition_model, create_deployment, test_prediction)
    retrain_info >> Label('Run ID & Artifact Location') >> create_model_version

    retrain_info >> branch_choice >> [create_registered_model, send_alert]


retrain = retrain()
