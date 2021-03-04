from flask import Flask
import threading
from veradata import veradata

app = Flask(__name__)

@app.route('/isready')
def isReady():
    return "OK"


@app.route('/isalive')
def isAlive():
    return "OK"


if __name__ == "__main__":
    threading.Thread(target=veradata().run, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
