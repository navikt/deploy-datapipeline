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
        logger.info("get data from vera")
        start = time.time()
        response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        # response = requests.get("https://vera.adeo.no/api/v1/deploylog?environment=p&csv=true")
        end = time.time()
        logger.info("vera.time " + str(end - start) + " seconds. ")
        logger.info("vera.size " + str(len(response.content)) + " bytes. ")
        return response.content

    def writecodetobucket(self, bytes):
        client = storage.Client()
        bucket = client.get_bucket("deployments-vera")
        today = datetime.date.today()
        date = today.strftime("%b-%d-%Y")
        blob_name = date + "deploys-vera.csv"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(str(bytes))
        return blob_name

    def write_vera_history_to_bq(self, filename):
        client = bigquery.Client()
        print("Acting as: " + client.get_service_account_email())
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

        source_uri = "gs://deployments-vera/" + filename
        print(source_uri)
        table_id = "nais-analyse-prod-2dcc.deploys.vera-deploys"
        load_job = client.load_table_from_uri(source_uri, table_id, job_config=job_config)
        load_job.result()

        destination_table = client.get_table(table_id)  # Make an API request.
        print("Loaded {} rows.".format(destination_table.num_rows))



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
