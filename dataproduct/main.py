#!/usr/bin/env python
import logging
import signal
import sys

from endpoints import start_server

class ExitOnSignal(Exception):
    pass

def signal_handler(signum, frame):
    raise ExitOnSignal()



def main():
    print("Starting main")

    from dataproduct import BigqueryLoader as _p

    server = start_server()
    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal_handler)
        try:
            exit_code = _p.run()
        except ExitOnSignal:
            exit_code = 0
        except Exception as e:
            logging.exception(f"unwanted exception: {e}")
            exit_code = 113
    finally:
        server.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()