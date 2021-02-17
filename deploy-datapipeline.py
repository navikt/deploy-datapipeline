from flask import Flask
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import time
import threading
import atexit
import requests
import logging
from google.cloud import storage

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
        # response = requests.get("https://vera.nais.oera.no/api/v1/deploylog?environment=p&csv=true")
        response = requests.get("https://vera.adeo.no/api/v1/deploylog?environment=p&csv=true")
        end = time.time()
        logger.info("vera.time " + str(end - start) + " seconds. ")
        logger.info("vera.size " + str(len(response.content)) + " bytes. ")
        return response.content

    def writecodetobucket(self, bytes):
        client = storage.Client()
        bucket = client.get_bucket("deplioyments.vera")
        blob = bucket.blob("name of blob")
        blob.upload_from_string(str(bytes))


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
        vera.writecodetobucket(bytes)
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
    print("test")
    logger.info("starting service")
    app.run(host='0.0.0.0', port=8080)
