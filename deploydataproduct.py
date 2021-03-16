from google.cloud import storage
import datetime
import time
import requests
import logging
import pandas


BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeployDataProduct():

    def run(self):
        # Wait for istio
        time.sleep(30)

        output_filename = datetime.date.today().strftime("%Y-%m-%d") + "-deploys-vera.parquet"
        csv = self.get_deploydata_from_vera()
        self.transform(csv, output_filename)
        return self.write_to_bucket(output_filename)

    def get_deploydata_from_vera(self):
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("vera: Time: {} seconds, size {}".format(str(time.time() - start), str(len(response.content))))
        return response.text

    def write_to_bucket(self, parquet_filename):
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        bucket.blob(parquet_filename).upload_from_file(parquet_filename)
        return "gs://" + BUCKET_NAME + "/" + parquet_filename

    def transform(self, csv, parquet_filename):
        df = pandas.read_csv(csv)
        df['deployed_timestamp'] = pandas.to_datetime(df['deployed_timestamp'], format='%Y-%m-%d %H:%M:%S')
        df['replaced_timestamp'] = pandas.to_datetime(df['replaced_timestamp'], format='%Y-%m-%d %H:%M:%S')
        df.to_parquet(parquet_filename)
