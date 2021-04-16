from google.cloud import storage
import datetime
import time
import requests
import logging
import pandas
from io import StringIO
import pytz


BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"
DATA_CATALOG_API = "https://datakatalog-api.intern.nav.no/v1/index"
DATA_PRODUCT_ID = 'f55023cf-4acc-48a2-9a98-a04e4c0aea70'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeployDataProduct():

    def run(self):
        logger.info('Wait 30 seconds for Istio to get going...')
        time.sleep(30)

        output_filename = datetime.date.today().strftime("%Y-%m-%d") + "-deploys-vera.parquet"
        csv_text = self.get_deploydata_from_vera()
        self.transform(csv_text, output_filename)
        uri = self.write_to_bucket(output_filename)
        self.post_metadata(uri)
        return output_filename

    def get_deploydata_from_vera(self):
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("Get data from vera: Time: {} seconds, size {}".format(str(time.time() - start), str(len(response.content))))
        logger.info(response.content)
        return response.text

    def write_to_bucket(self, parquet_filename):
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        with open(parquet_filename, 'rb') as file:
            bucket.blob(parquet_filename).upload_from_file(file)
        return f'gs://{BUCKET_NAME}/{parquet_filename}'

    def transform(self, csv_text, parquet_filename):
        df = pandas.read_csv(StringIO(csv_text))
        df['deployed_timestamp'] = pandas.to_datetime(df['deployed_timestamp'], format='%Y-%m-%d %H:%M:%S')
        df['replaced_timestamp'] = pandas.to_datetime(df['replaced_timestamp'], format='%Y-%m-%d %H:%M:%S')
        df.to_parquet(parquet_filename)

    def post_metadata(self, uri):
        now = datetime.datetime.now(pytz.timezone('Europe/Oslo')).isoformat()
        metadata = {
            'id': DATA_PRODUCT_ID,
            'title': 'Deploys til prod',
            'description': 'Alle deploys av applikasjoner til prod siden 2009',
            'type': 'egg',
            'uri': uri,
            'modified': now
        }

        response = requests.put(DATA_CATALOG_API, json=metadata)
        logger.info(f'Putting metadata in data catalog: {response.status_code} - {response.content}')
