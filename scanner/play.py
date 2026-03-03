"""Play Framework scanner - Detect endpoints in Scala Play applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class PlayScanner(APIScanner):
    """Scan Play Framework projects for API endpoints."""
    
    def scan(self):
        """Scan Play routes and controllers."""
        # Scan conf/routes
        routes_file = os.path.join(self.project_path, "conf", "routes")
        if os.path.exists(routes_file):
            self._scan_routes(routes_file)
        
        # Scan app/controllers
        controllers_dir = os.path.join(self.project_path, "app", "controllers")
        if os.path.exists(controllers_dir):
            for root, dirs, files in os.walk(controllers_dir):
                for file in files:
                    if file.endswith(".scala") or file.endswith(".java"):
                        self._scan_file(os.path.join(root, file))
        
        return self.endpoints
    
    def _scan_routes(self, filepath):
        """Extract from Play routes file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # GET /users controllers.UserController.index
            method_pattern = r"^(\w+)\s+(/\S+)"
            matches = re.finditer(method_pattern, content, re.MULTILINE)
            
            for match in matches:
                method = match.group(1)
                path = match.group(2)
                endpoint = Endpoint(path, method, filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
    
    def _scan_file(self, filepath):
        """Extract from controller files."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # def index = Action { ... }
            action_pattern = r"def\s+(\w+)\s*="
            matches = re.finditer(action_pattern, content)
            
            for match in matches:
                action = match.group(1)
                endpoint = Endpoint(f"/action/{action}", "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
