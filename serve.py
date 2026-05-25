import json
import os
import sys
from RangeHTTPServer import RangeRequestHandler
from http.server import HTTPServer

config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
with open(config_path) as f:
    config = json.load(f)

port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
files_path = config["files_path"]

class QuietServer(HTTPServer):
    def handle_error(self, request, client_address):
        if issubclass(sys.exc_info()[0], BrokenPipeError):
            return
        super().handle_error(request, client_address)


os.chdir(files_path)
server = QuietServer(("", port), RangeRequestHandler)
print(f"Serving {files_path} at http://localhost:{port}/")
server.serve_forever()
