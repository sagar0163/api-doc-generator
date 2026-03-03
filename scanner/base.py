"""Core scanner module - Base classes for API detection"""


class APIScanner:
    """Base class for API endpoint scanners."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.endpoints = []
    
    def scan(self):
        """Scan project for API endpoints."""
        raise NotImplementedError
    
    def get_endpoints(self):
        """Return discovered endpoints."""
        return self.endpoints


class Endpoint:
    """Represents a single API endpoint."""
    
    def __init__(self, path, method, handler):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.description = ""
        self.parameters = []
        self.responses = {}
    
    def to_dict(self):
        return {
            "path": self.path,
            "method": self.method,
            "handler": self.handler,
            "description": self.description,
            "parameters": self.parameters,
            "responses": self.responses
        }

