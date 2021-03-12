from flask import Flask
import threading
from deploydataproduct import DeployDataProduct
from datapakke import DeployDataPakke
import time

app = Flask(__name__)


@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"


def run():
    time.sleep(10)
    #produkt = DeployDataProduct()
    pakke = DeployDataPakke()
    # address = DeployDataProduct.run()
    address = "gs://deployments-vera/2021-03-11-deploys-vera.csv"
    pakke.publiser_datapakke(address)


if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
