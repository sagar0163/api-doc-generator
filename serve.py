"""Offline preview server for generated API documentation.

Serves the same self-contained Swagger UI page produced by
``apidocgen export --html``: all assets (CSS, JS, spec JSON) are inline, so
the served page makes no CDN / network requests. No files are written to
the spec's directory; everything is served from memory.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from generator.html import build_standalone_html


class SwaggerUIHandler(BaseHTTPRequestHandler):
    """Serve the standalone Swagger UI page plus the raw spec."""

    html = None
    spec = None

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html", "/docs"):
            body = self.html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/openapi.json":
            body = self.spec.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):  # noqa: A003 - keep server output quiet
        print("[apidocgen] {} {}".format(
            self.command, self.path.split("?", 1)[0].split("/", 1)[-1] or "/"
        ))


def build_page(spec_path, title=None):
    """Load a spec file and build the self-contained HTML page for it."""
    spec_path = Path(spec_path)
    with open(spec_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if spec_path.suffix.lower() in (".yaml", ".yml"):
        import yaml
        spec_dict = yaml.safe_load(raw)
        spec = json.dumps(spec_dict, indent=2)
    else:
        spec = raw
    html = build_standalone_html(spec, title=title or "API Documentation")
    return html, spec


def serve(spec_path="openapi.json", port=8000, host="127.0.0.1", title=None):
    """Start a local server serving the standalone Swagger UI page."""
    html, spec = build_page(spec_path, title=title)

    SwaggerUIHandler.html = html
    SwaggerUIHandler.spec = spec

    server = HTTPServer((host, port), SwaggerUIHandler)

    print("API Documentation server running at:")
    print(f"   http://{host}:{port}")
    print(f"   Swagger UI: http://{host}:{port}/docs")
    print(f"   Raw spec:   http://{host}:{port}/openapi.json")
    print("\nPress Ctrl+C to stop the server")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Serve API Documentation")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument("-s", "--spec", default="openapi.json", help="Path to OpenAPI spec")
    parser.add_argument("-t", "--title", default=None, help="Page title override")

    args = parser.parse_args()
    serve(args.spec, args.port, title=args.title)