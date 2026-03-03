"""Laravel scanner - Detect endpoints in Laravel applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class LaravelScanner(APIScanner):
    """Scan Laravel projects for API endpoints."""
    
    def scan(self):
        """Scan Laravel routes and controllers."""
        # Scan routes/api.php
        routes_file = os.path.join(self.project_path, "routes", "api.php")
        if os.path.exists(routes_file):
            self._scan_routes(routes_file)
        
        # Scan routes/web.php
        web_routes = os.path.join(self.project_path, "routes", "web.php")
        if os.path.exists(web_routes):
            self._scan_routes(web_routes)
        
        return self.endpoints
    
    def _scan_routes(self, filepath):
        """Extract routes from Laravel route files."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Route::get('/users', ...)
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                pattern = rf"Route::{method}\(['\"]([^'\"]+)['\"]"
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # Route::resource('photos', ...)
            resource_pattern = r"Route::resource\(['\"](\w+)['\"]"
            matches = re.finditer(resource_pattern, content)
            
            for match in matches:
                resource = match.group(1)
                for method in ["GET", "POST", "PUT", "DELETE"]:
                    endpoint = Endpoint(f"/{resource}", method, filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
