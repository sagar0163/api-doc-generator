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
        self.schemas = {}
    
    def add_endpoint(self, endpoint):
        """Add an endpoint to the spec."""
        self.endpoints.append(endpoint)
    
    def add_server(self, url, description=None):
        """Add a server URL."""
        server = {"url": url}
        if description:
            server["description"] = description
        self.servers.append(server)

    def add_schema(self, name, schema):
        """Add a component schema."""
        self.schemas[name] = schema
    
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
        if self.schemas:
            spec["components"] = {"schemas": self.schemas}
        
        return spec
    
    def _normalize_path(self, path):
        import re
        # Flask: <type:name> or <name>
        path = re.sub(r'<[^>:]+:([^>]+)>', r'{\1}', path)
        path = re.sub(r'<([^>]+)>', r'{\1}', path)
        # Express: :name
        # Be careful not to replace https://... but paths usually start with /
        # We only match path segments starting with :
        path = re.sub(r'(?<=/):([a-zA-Z0-9_]+)', r'{\1}', path)
        return path

    def _generate_paths(self):
        """Convert endpoints to OpenAPI paths format."""
        paths = {}
        
        for endpoint in self.endpoints:
            path = self._normalize_path(endpoint.path)
            method = endpoint.method.lower()
            
            # OpenAPI only supports specific methods
            if method not in ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']:
                continue
            
            if path not in paths:
                paths[path] = {}
            
            paths[path][method] = {
                "summary": endpoint.handler,
                "description": endpoint.description or f"Endpoint: {path}",
                "parameters": endpoint.parameters or [],
                "responses": endpoint.responses or {
                    "200": {"description": "Successful response"}
                }
            }
            if hasattr(endpoint, 'requestBody') and endpoint.requestBody:
                paths[path][method]['requestBody'] = endpoint.requestBody
        
        return paths
    
    def to_json(self, indent=2):
        """Export to JSON format."""
        return json.dumps(self.generate(), indent=indent)
    
    def to_yaml(self):
        """Export to YAML format."""
        import yaml
        return yaml.dump(self.generate(), default_flow_style=False)
