"""AdonisJS scanner - Detect endpoints in AdonisJS applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class AdonisScanner(APIScanner):
    """Scan AdonisJS projects for API endpoints."""
    
    def scan(self):
        """Scan Adonis routes."""
        # Scan start/routes.ts
        routes_file = os.path.join(self.project_path, "start", "routes.ts")
        if os.path.exists(routes_file):
            self._scan_file(routes_file)
        
        # Also check start/routes.js
        routes_js = os.path.join(self.project_path, "start", "routes.js")
        if os.path.exists(routes_js):
            self._scan_file(routes_js)
        
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Adonis routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Route.get('/users', 'UserController.index')
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                # Route.method('/path', 'Controller.action')
                pattern = rf"Route\.{method}\(['\"]([^'\"]+)['\"]"
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # Route.resource('/users', 'UserController')
            resource_pattern = r"Route\.resource\(['\"]([^'\"]+)['\"]"
            matches = re.finditer(resource_pattern, content)
            
            for match in matches:
                resource = match.group(1)
                for method in ["GET", "POST", "PUT", "DELETE"]:
                    endpoint = Endpoint(f"/{resource}", method, filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
