from flask import Flask
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import threading
import atexit

POOL_TIME = 5 #Seconds

# thread handler
yourThread = threading.Thread()

def createApp():
    app = Flask(__name__)

    def interrupt():
        global yourThread
        yourThread.cancel()

    def getdeploydatafrominflux():
        print("starting thread")
        global yourThread

        client = DataFrameClient('influxdb.adeo.no', 8086, 'tmp123', 'tmp123', 'metrics')
        query = """    
            SELECT * 
            FROM "nais.deployment" 
            WHERE ("team" =~ /.+/ 
            AND "team" != 'aura'
            AND "rollout_status" = 'complete' 
            AND "environment" = "production")
        """
        result = client.query(query)
        df = pd.concat(result).reset_index()
        print(df.head())
        # Set the next thread to happen
        # yourThread = threading.Timer(POOL_TIME, getdeploydatafrominflux(), ())
        # yourThread.start()

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread
        # Create your thread
        yourThread = threading.Timer(POOL_TIME, getdeploydatafrominflux, ())
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
    threading.Thread(app.run(host='0.0.0.0', port=8080)).start()
    print("started service")
