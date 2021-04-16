import flask
from flask import Flask
import threading
from datetime import datetime as dt
from deploydataproduct import DeployDataProduct
from datapakke import DeployDataPakke

app = Flask(__name__)
start_time = dt.now()

@app.route('/isready')
def isReady():
    return flask.Response(status=200)


@app.route('/isalive')
def isAlive():
    # Force k8s to restart the app every 24h as a super hacky scheduler for updating the data package
    uptime = (dt.now() - start_time).total_seconds()
    status = 500 if uptime > 60*60*24 else 200
    return flask.Response(status=status)


def run():
    produkt = DeployDataProduct()
    dataproduct_filename = produkt.run()
    pakke = DeployDataPakke()
    pakke.publiser_datapakke(dataproduct_filename)


if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
