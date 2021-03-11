from google.cloud import storage
import datetime
import time
import requests
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

BUCKET_NAME = "deployments-vera"
PROJECT = "nais-analyse-prod-2dcc"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeployDataProduct():

    def run(self):
        data = self.getdeploydatafromvera()
        return self.writecodetobucket(data)

    def getdeploydatafromvera(self):
        start = time.time()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)

        response = http.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("vera: Time: {} seconds, size {}".format(str(time.time() - start), str(len(response.content))))
        return response.text

    def writecodetobucket(self, file_as_string):
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob_name = datetime.date.today().strftime("%Y-%m-%d") + "-deploys-vera.csv"
        bucket.blob(blob_name).upload_from_string(file_as_string, content_type="text/csv")
        return "gs://" + BUCKET_NAME + "/" + blob_name
