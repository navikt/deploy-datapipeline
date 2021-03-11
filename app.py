from flask import Flask
import threading
from deploydataproduct import DeployDataProduct

app = Flask(__name__)

@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"

def run():
    address = DeployDataProduct.run()



if __name__ == "__main__":
    threading.Thread(target=DeployDataProduct().run, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
