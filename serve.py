"""Live preview server for generated API documentation"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class SwaggerUIHandler(SimpleHTTPRequestHandler):
    """Serve Swagger UI with generated OpenAPI spec."""
    
    def do_GET(self):
        if self.path == "/" or self.path == "/docs":
            self.path = "/index.html"
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


def generate_swagger_index(openapi_json_path):
    """Generate Swagger UI HTML."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.0.0/swagger-ui.css" />
    <style>
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.0.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: 'openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>"""


def serve(spec_path="openapi.json", port=8000):
    """
    Start a local server with Swagger UI.
    
    Args:
        spec_path: Path to OpenAPI JSON file
        port: Port to serve on
    """
    # Get directory of spec file
    spec_dir = Path(spec_path).parent
    os.chdir(spec_dir)
    
    # Generate Swagger UI index
    index_path = Path(spec_dir) / "index.html"
    index_path.write_text(generate_swagger_index(spec_path))
    
    # Start server
    server = HTTPServer(('localhost', port), SwaggerUIHandler)
    
    print(f"🚀 API Documentation server running at:")
    print(f"   http://localhost:{port}")
    print(f"   Swagger UI: http://localhost:{port}/docs")
    print(f"\nPress Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Serve API Documentation")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument("-s", "--spec", default="openapi.json", help="Path to OpenAPI spec")
    
    args = parser.parse_args()
    serve(args.spec, args.port)
