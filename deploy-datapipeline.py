from flask import Flask
import time
import threading
import atexit
import requests
import logging
from google.cloud import storage, bigquery
import datetime

POOL_TIME = 5  # Seconds

# thread handler
yourThread = threading.Thread()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class veradata():

    def getdeploydatafromvera(self):
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        logger.info("vera: Time: {} seconds, size {}".format(str(time.time() - start)), str(len(response.content)))
        return str(response.content, encoding="utf-8")

    def writecodetobucket(self, file_as_string):
        client = storage.Client()
        bucket = client.get_bucket("deployments-vera")
        blob_name = datetime.date.today().strftime("%b-%d-%Y") + "-deploys-vera.csv"
        bucket.blob(blob_name).upload_from_string(file_as_string, content_type="text/csv")
        return blob_name

    def write_vera_history_to_bq(self, filename):
        client = bigquery.Client(project="nais-analyse-prod-2dcc", location='europe-north1')
        load_job = \
            client.load_table_from_uri(
                "gs://deployments-vera/" + filename,
                "nais-analyse-prod-2dcc.deploys.vera-deploys",
                job_config=(bigquery.LoadJobConfig(
                    skip_leading_rows=1,
                    source_format=bigquery.SourceFormat.CSV,
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                )))

        logger.info(f"Starting job {load_job.job_id} in project {load_job.project}")
        load_job.result()
        destination_table = client.get_table("nais-analyse-prod-2dcc.deploys.vera-deploys")
        logger.info("Loaded {} rows.".format(destination_table.num_rows))


def createApp():
    app = Flask(__name__)
    vera = veradata()

    logger.info("create app")

    def interrupt():
        global yourThread
        yourThread.cancel()

    def getdeploydatafromvera():
        global yourThread
        bytes = vera.getdeploydatafromvera()
        blobname = vera.writecodetobucket(bytes)
        vera.write_vera_history_to_bq(blobname)

        # Set the next thread to happen
        # yourThread = threading.Timer(POOL_TIME, getdeploydatafromvera(), ())
        # yourThread.start()

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread
        logger.info("do stuff start")

        # Create your thread
        yourThread = threading.Timer(POOL_TIME, getdeploydatafromvera, ())
        yourThread.start()

    # Initiate
    doStuffStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app


app = createApp()


@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"


if __name__ == "__main__":
    logger.info("starting service")
    app.run(host='0.0.0.0', port=8080)
