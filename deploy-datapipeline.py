from flask import Flask
from influxdb import InfluxDBClient, DataFrameClient
import pandas as pd
import threading

app = Flask(__name__)


@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"


def getdeploydatafrominflux():
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


if __name__ == "__main__":
    threading.Thread(app.run(host='0.0.0.0', port=8080)).start()
    print("test")
    getdeploydatafrominflux()
