import logging
import requests
import json
import ast


class LogstashHandler(logging.Handler):
    def __init__(self, host, port):
        super().__init__()
        self.url = f"http://{host}:{port}"
    def emit(self, record):
        log_entry = ast.literal_eval(self.format(record))
        try:
            requests.post(
                self.url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "ACCOUNT": log_entry.get('ACCOUNT', None),
                    "LOG": {
                        "TYPE": log_entry.get('TYPE', None),
                        "DESC": log_entry.get('DESC', None)
                    },
                    "LEVEL": record.levelname,
                    "PLATFORM": log_entry.get('PLATFORM', None)
                })
            )
        except Exception as e:
            print(f"Failed to send log: {e}")


logger = logging.getLogger("logstash")
logger.setLevel(logging.INFO)
# logger.addHandler(LogstashHandler("192.168.10.50", 5000))
