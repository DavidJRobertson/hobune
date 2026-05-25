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

os.chdir(files_path)
server = HTTPServer(("", port), RangeRequestHandler)
print(f"Serving {files_path} at http://localhost:{port}/")
server.serve_forever()
