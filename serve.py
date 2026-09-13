"""Live preview server for generated API documentation"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


from generator.html import generate_standalone_html

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
    
    # Read the spec
    with open(Path(spec_path).name, "r", encoding="utf-8") as f:
        spec_dict = json.load(f)
        
    # Generate Swagger UI index
    index_path = Path(spec_dir) / "index.html"
    index_path.write_text(generate_standalone_html(spec_dict))
    
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
