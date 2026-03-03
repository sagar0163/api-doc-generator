"""Sails scanner - Detect endpoints in Sails.js applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class SailsScanner(APIScanner):
    """Scan Sails.js projects for API endpoints."""
    
    def scan(self):
        """Scan Sails controllers and routes."""
        # Scan api/controllers
        controllers_dir = os.path.join(self.project_path, "api", "controllers")
        if os.path.exists(controllers_dir):
            for root, dirs, files in os.walk(controllers_dir):
                for file in files:
                    if file.endswith(".js"):
                        self._scan_file(os.path.join(root, file))
        
        # Scan config/routes.js
        routes_file = os.path.join(self.project_path, "config", "routes.js")
        if os.path.exists(routes_file):
            self._scan_routes(routes_file)
        
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract from Sails controller."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # module.exports = { find: function(req, res) { ... }
            action_pattern = r"module\.exports\s*=\s*\{([^}]+)\}"
            matches = re.finditer(action_pattern, content)
            
            for match in matches:
                actions = match.group(1)
                # Find action names
                action_names = re.findall(r"(\w+):\s*function", actions)
                for action in action_names:
                    endpoint = Endpoint(f"/action/{action}", "GET", filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
    
    def _scan_routes(self, filepath):
        """Extract from routes config."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # "GET /users": { controller: 'UserController', action: 'find' }
            route_pattern = r"['\"](\w+)\s+(/\w+)['\"]:\s*\{"
            matches = re.finditer(route_pattern, content)
            
            for match in matches:
                method = match.group(1)
                path = match.group(2)
                endpoint = Endpoint(path, method, filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
