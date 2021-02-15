from flask import Flask

app = Flask(__name__)

@app.route('/isReady')
def isReady():
    return "OK"

@app.route('/isAlive')
def isAlive():
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
    print("hello worlds")