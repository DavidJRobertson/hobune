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


class HobuneHandler(RangeRequestHandler):
    def do_GET(self):
        if self.path.startswith("/dl/") or self.path == "/dl":
            self._serve_download()
        else:
            super().do_GET()

    def _serve_download(self):
        # Strip /dl prefix and translate to a filesystem path the same way the
        # normal handler would, so files_web_path → files_path mapping is correct.
        original_path = self.path
        self.path = self.path[len("/dl"):]
        file_path = self.translate_path(self.path)
        self.path = original_path

        if not os.path.isfile(file_path):
            self.send_error(404)
            return

        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                self.wfile.write(chunk)


class QuietServer(HTTPServer):
    def handle_error(self, request, client_address):
        if issubclass(sys.exc_info()[0], BrokenPipeError):
            return
        super().handle_error(request, client_address)


os.chdir(files_path)
server = QuietServer(("", port), HobuneHandler)
print(f"Serving {files_path} at http://localhost:{port}/")
server.serve_forever()
