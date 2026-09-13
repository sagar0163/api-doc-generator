"""OpenAPI generator - Generate OpenAPI/Swagger specifications"""

import json
from datetime import datetime


class OpenAPIGenerator:
    """Generate OpenAPI 3.0 specifications from discovered endpoints."""
    
    def __init__(self, title="API Documentation", version="1.0.0"):
        self.title = title
        self.version = version
        self.endpoints = []
        self.servers = []
    
    def add_endpoint(self, endpoint):
        """Add an endpoint to the spec."""
        self.endpoints.append(endpoint)
    
    def add_server(self, url, description=None):
        """Add a server URL."""
        server = {"url": url}
        if description:
            server["description"] = description
        self.servers.append(server)
    
    def generate(self):
        """Generate OpenAPI specification."""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": f"Auto-generated API documentation"
            },
            "servers": self.servers if self.servers else [{"url": "http://localhost:3000"}],
            "paths": self._generate_paths()
        }
        
        return spec
    
    def _generate_paths(self):
        """Convert endpoints to OpenAPI paths format."""
        paths = {}
        
        for endpoint in self.endpoints:
            path = endpoint.path
            
            if path not in paths:
                paths[path] = {}
            
            method = endpoint.method.lower()
            
            paths[path][method] = {
                "summary": endpoint.handler,
                "description": endpoint.description or f"Endpoint: {endpoint.path}",
                "parameters": endpoint.parameters,
                "responses": endpoint.responses or {
                    "200": {"description": "Successful response"}
                }
            }
        
        return paths
    
    def to_json(self, indent=2):
        """Export to JSON format.

        Keys are always emitted in sorted order so identical specs produce
        byte-identical files (safe for CI diffing).  A single trailing
        newline is appended for parity with ``to_yaml``.
        """
        return json.dumps(self.generate(), indent=indent, sort_keys=True) + "\n"
    
    def to_yaml(self):
        """Export to YAML format.

        ``sort_keys=True`` keeps key order deterministic across runs, so
        identical specs always serialize to identical bytes.
        """
        import yaml
        return yaml.safe_dump(
            self.generate(), default_flow_style=False, sort_keys=True
        )
