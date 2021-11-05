import logging
import threading

import flask
from werkzeug.serving import make_server

LOG = logging.getLogger(__name__)


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server("0.0.0.0", 8080, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        LOG.info("starting server")
        self.server.serve_forever()

    def shutdown(self):
        LOG.info("stopping server")
        self.server.shutdown()


def start_server():
    app = flask.Flask('healthz')

    @app.route("/isHealthy")
    def healthy():
        return "Healthy as a fish"

    @app.route("/isReady")
    def ready():
        return "Ready as an egg"

    server = ServerThread(app)
    server.start()
    return server