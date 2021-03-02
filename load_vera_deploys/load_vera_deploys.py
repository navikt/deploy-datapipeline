from google.cloud import bigquery


def write_vera_history_to_bq():
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("environment", "STRING"),
            bigquery.SchemaField("application", "STRING"),
            bigquery.SchemaField("version", "STRING"),
            bigquery.SchemaField("deployer", "STRING"),
            bigquery.SchemaField("deployed_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("replaced_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("environmentClass", "STRING"),
            bigquery.SchemaField("id", "STRING")
        ],
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV
    )

    source_uri = "gs://deployments-vera/Mar-01-2021deploys-vera.csv"
    table_id = "nais-analyse-prod-2dcc:deploys.vera_deploys"
    load_job = client.load_table_from_uri(source_uri, table_id, job_config=job_config)
    load_job.result()

    destination_table = client.get_table(table_id)  # Make an API request.
    print("Loaded {} rows.".format(destination_table.num_rows))
