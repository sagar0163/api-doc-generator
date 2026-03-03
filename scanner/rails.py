"""Ruby on Rails scanner - Detect endpoints in Rails applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class RailsScanner(APIScanner):
    """Scan Rails projects for API endpoints."""
    
    def scan(self):
        """Scan Rails routes and controllers."""
        # Scan config/routes.rb
        routes_file = os.path.join(self.project_path, "config", "routes.rb")
        if os.path.exists(routes_file):
            self._scan_routes(routes_file)
        
        # Scan controllers
        controllers_dir = os.path.join(self.project_path, "app", "controllers")
        if os.path.exists(controllers_dir):
            for root, dirs, files in os.walk(controllers_dir):
                for file in files:
                    if file.endswith(".rb"):
                        self._scan_file(os.path.join(root, file))
        
        return self.endpoints
    
    def _scan_routes(self, filepath):
        """Extract routes from routes.rb."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # resources :users
            resources_pattern = r"resources\s+:(\w+)"
            matches = re.finditer(resources_pattern, content)
            
            for match in matches:
                resource = match.group(1)
                # Standard REST routes
                for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = Endpoint(f"/{resource}", method, filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
    
    def _scan_file(self, filepath):
        """Extract from controller files."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # def show, def index, etc.
            method_pattern = r"def\s+(\w+)"
            matches = re.finditer(method_pattern, content)
            
            for match in matches:
                method_name = match.group(1)
                endpoint = Endpoint(f"/action/{method_name}", "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
