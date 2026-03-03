"""Phoenix scanner - Detect endpoints in Elixir Phoenix applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class PhoenixScanner(APIScanner):
    """Scan Phoenix projects for API endpoints."""
    
    def scan(self):
        """Scan Phoenix router and controllers."""
        # Scan router.ex
        router_file = os.path.join(self.project_path, "lib", "app_name", "web", "router.ex")
        if os.path.exists(router_file):
            self._scan_router(router_file)
        
        # Also check lib/*/web/router.ex
        lib_dir = os.path.join(self.project_path, "lib")
        if os.path.exists(lib_dir):
            for root, dirs, files in os.walk(lib_dir):
                if "router.ex" in files:
                    self._scan_router(os.path.join(root, "router.ex"))
        
        return self.endpoints
    
    def _scan_router(self, filepath):
        """Extract from Phoenix router."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # get "/users", UserController, :index
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                pattern = rf'{method}\s+["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # resources "/users", UserController
            resources_pattern = r'resources\s+["\']([^"\']+)["\']'
            matches = re.finditer(resources_pattern, content)
            
            for match in matches:
                path = match.group(1)
                for method in ["GET", "POST", "PUT", "DELETE"]:
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
