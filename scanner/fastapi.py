"""FastAPI scanner - Detect endpoints in FastAPI applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class FastAPIScanner(APIScanner):
    """Scan FastAPI projects for API endpoints."""
    
    def scan(self):
        """Scan directory for FastAPI routes."""
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract FastAPI routes from Python file."""
        with open(filepath, "r") as f:
            content = f.read()
        
        # Find @app.get(), @app.post(), etc.
        methods = ["get", "post", "put", "delete", "patch"]
        
        for method in methods:
            pattern = rf"@(?:app|router)\.{method}\(['\"]([^'\"]+)['\"]"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, method.upper(), filepath)
                self.endpoints.append(endpoint)
        
        # Find @app.route() with methods parameter
        route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?"
        matches = re.finditer(route_pattern, content)
        
        for match in matches:
            path = match.group(1)
            methods_list = match.group(2) or "GET"
            methods_list = [m.strip().strip("'\"") for m in methods_list.split(",")]
            
            for m in methods_list:
                endpoint = Endpoint(path, m.upper(), filepath)
                self.endpoints.append(endpoint)
