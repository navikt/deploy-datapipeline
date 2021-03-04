from google.cloud import storage, bigquery
import datetime
import time
import requests
import logging

BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class veradata():

    def run(self):
        data = self.getdeploydatafromvera()
        filename = self.writecodetobucket(data)
        self.write_vera_history_to_bq(filename)

    def getdeploydatafromvera(self):
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("vera: Time: {} seconds, size {}".format(str(time.time() - start), str(len(response.content))))
        return response.text

    def writecodetobucket(self, file_as_string):
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob_name = datetime.date.today().strftime("%b-%d-%Y") + "-deploys-vera.csv"
        bucket.blob(blob_name).upload_from_string(file_as_string, content_type="text/csv")
        return blob_name

    def write_vera_history_to_bq(self, filename):
        client = bigquery.Client(project=PROJECT, location='europe-north1')
        load_job = \
            client.load_table_from_uri(
                "gs://" + BUCKET_NAME + "/" + filename,
                PROJECT + ".deploys.vera-deploys",
                job_config=(bigquery.LoadJobConfig(
                    skip_leading_rows=1,
                    source_format=bigquery.SourceFormat.CSV,
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                )))

        logger.info(f"Starting job {load_job.job_id} in project {load_job.project}")
        load_job.result()
        destination_table = client.get_table("nais-analyse-prod-2dcc.deploys.vera-deploys")
        logger.info("Loaded {} rows.".format(destination_table.num_rows))
