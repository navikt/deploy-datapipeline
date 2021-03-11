from google.cloud import storage, bigquery
import datetime
import time
import requests
import logging
import datapakke

BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class veradata():

    def run(self):
        data = self.getdeploydatafromvera()
        fileURI = self.writecodetobucket(data)
        datapakke.publiser_datapakke(fileURI)

    def getdeploydatafromvera(self):
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("vera: Time: {} seconds, size {}".format(str(time.time() - start), str(len(response.content))))
        return response.text

    def writecodetobucket(self, file_as_string):
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob_name = datetime.date.today().strftime("%Y-%m-%d") + "-deploys-vera.csv"
        bucket.blob(blob_name).upload_from_string(file_as_string, content_type="text/csv")
        return "gs://" + BUCKET_NAME + "/" + blob_name

