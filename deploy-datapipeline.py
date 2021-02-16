from flask import Flask
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import threading
import atexit
import requests

POOL_TIME = 5 #Seconds

# thread handler
yourThread = threading.Thread()

def createApp():
    app = Flask(__name__)

    def interrupt():
        global yourThread
        yourThread.cancel()

    def getdeploydatafromvera():
        print("starting thread")
        global yourThread

        response = requests.get("https://vera.adeo.no/api/v1/deploylog?environment=p&csv=true&last=1d")

        print(response.headers)
        # Set the next thread to happen
        # yourThread = threading.Timer(POOL_TIME, getdeploydatafromvera(), ())
        # yourThread.start()

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread
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
    print("starting service")
    app.run(host='0.0.0.0', port=8080)