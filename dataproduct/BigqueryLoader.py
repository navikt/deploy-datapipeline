import datetime
import logging

import pandas
from google.cloud import bigquery
from google.cloud.bigquery import DatasetReference, TableReference

import parquetFile
from dataproduct.bucket import downloadFile

LOG = logging.getLogger(__name__)

PROJECT = "nais-analyse-prod-2dcc"
DATASET = "deployments"
ARCHIVED_DEPLOYS = "2021-04-01-deploys-vera.parquet"


def run():
    _init_bq()
    print("Starting Bigquery Loader")
    # archive = "2021-04-01-deploys-vera.parquet"
    archive = downloadFile(ARCHIVED_DEPLOYS)
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d") + "-deploys-vera-since-2021.parquet"
    latestFile = downloadFile(yesterday)
    # latestFile = "2021-11-04-deploys-vera-since-2021.parquet"

    archive_df = parquetFile.create_dataframe(archive)
    latest_df = parquetFile.create_dataframe(latestFile)
    archive_df.append(latest_df)
    print(archive_df.size)

    return 0


def load_data(parquet):
    df = parquetFile.create_dataframe(parquet)
    print(df.size)
    print("Dataframe created")


def _init_bq():
    client = bigquery.Client()
    dataset_ref = DatasetReference(PROJECT, DATASET)
    table_ref = TableReference(dataset_ref, "dataproduct_apps")
    schema = [
        bigquery.SchemaField(name="id", field_type="ID"),
        bigquery.SchemaField(name="environment", field_type="STRING"),
        bigquery.SchemaField(name="application", field_type="STRING"),
        bigquery.SchemaField(name="version", field_type="STRING"),
        bigquery.SchemaField(name="deployer", field_type="STRING"),
        bigquery.SchemaField(name="team", field_type="STRING"),
        bigquery.SchemaField(name="deployed_timestampe", field_type="TIMESTAMP"),
        bigquery.SchemaField(name="replaced_timestampe", field_type="TIMESTAMP"),
    ]
    table = client.create_table(bigquery.Table(table_ref, schema=schema), exists_ok=True)
    return client, table
