MLflow Provdider Examples
========

DAGs:
- feature_eng.py: Synthetically creates features using iris dataset.
- monitor_features.py: Uses Evidently to monitor data drift in features after feature_eng DAG adds new features.
- retrain.py: Trains and registers a new model with MLflow and deploys it to SageMaker. Is triggered by the monitoring DAG.
- predict.py: Loads a model from MLflow and performs prediction with a given set of input data.
- generate_true_values.py: Synthetically generates feedback for target value.


Pre-Requisites
==============

1. Have [built and pushed](https://mlflow.org/docs/latest/cli.html?highlight=sagemaker%20build%20push#mlflow-sagemaker-build-and-push-container) an MLflow pyfunc image to AWS ECR. (This is used by the **retrain** DAG)
2. Have a Postgres DB setup with the tables listed below in the `public` schema. The [helper_files](helper_files) directory contains scripts to create each of these tables. 
    - iris_ground_truth
    - new_features
    - predictions
    - true_values
3. Populate the iris_ground_truth table with the accompanying CSV file [isis_ground_truth.csv](helper_files/iris_ground_truth.csv)


Connections and Variables
=========================

**Connections:**
- aws_default: AWS connection to access ECR and SageMaker
- mlflow_default: MLflow connection information using the HTTP connection type
- postgres: Postgres connection
- slack_default: Connection info for sending alerts via Slack Operator

**Variables:**
- mlflow_pyfunc_image_url: The ECR URI for your MLflow pyfunc image.
- sagemaker_execution_arn: The SageMaker execution arn

Project Contents
================

Your Astro project contains the following files and folders:

- dags: This folder contains the Python files for your Airflow DAGs. By default, this directory includes an example DAG that runs every 30 minutes and simply prints the current date. It also includes an empty 'my_custom_function' that you can fill out to execute Python code.
- Dockerfile: This file contains a versioned Astro Runtime Docker image that provides a differentiated Airflow experience. If you want to execute other commands or overrides at runtime, specify them here.
- include: This folder contains any additional files that you want to include as part of your project. It is empty by default.
- packages.txt: Install OS-level packages needed for your project by adding them to this file. It is empty by default.
- requirements.txt: Install Python packages needed for your project by adding them to this file. It is empty by default.
- plugins: Add custom or community plugins for your project to this file. It is empty by default.
- airflow_settings.yaml: Use this local-only file to specify Airflow Connections, Variables, and Pools instead of entering them in the Airflow UI as you develop DAGs in this project.
- helper_files: SQL files to get your started on the Postgres DB (makeshift feature store)
