from flask import Flask
import threading
import atexit
import veradata

POOL_TIME = 5  # Seconds

# thread handler
yourThread = threading.Thread()


def createApp():
    app = Flask(__name__)
    vera = veradata()

    def interrupt():
        global yourThread
        yourThread.cancel()

    def loadVeraDataIntoBigQuery():
        global yourThread
        vera.run()

    # Set the next thread to happen
    # yourThread = threading.Timer(POOL_TIME, loadVeraDataIntoBigQuery(), ())
    # yourThread.start()

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread

        # Create your thread
        yourThread = threading.Timer(POOL_TIME, loadVeraDataIntoBigQuery, ())
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
    app.run(host='0.0.0.0', port=8080)
