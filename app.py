from flask import Flask
import threading
from deploydataproduct import DeployDataProduct
from datapakke import DeployDataPakke

app = Flask(__name__)


@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"


def run():
    # address = DeployDataProduct.run()
    address = "gs://deployments-vera/2021-03-11-deploys-vera.csv"
    DeployDataPakke.publiser_datapakke(address)


if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
