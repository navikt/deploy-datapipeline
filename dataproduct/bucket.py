import logging
from google.cloud import storage

BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"


def downloadFile(filename):
    logging.info('initialize google storage client and access data product...')
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)

    blob = bucket.get_blob(filename)
    local_parquet_file = 'temp.parquet'

    with open(local_parquet_file, 'wb') as file:
        blob.download_to_file(file)

    return file
