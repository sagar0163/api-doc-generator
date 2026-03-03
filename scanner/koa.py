"""Koa scanner - Detect endpoints in Koa.js applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class KoaScanner(APIScanner):
    """Scan Koa projects for API endpoints."""
    
    def scan(self):
        """Scan Koa routes."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["node_modules", ".git"]]
            
            for file in files:
                if file.endswith(".js") or file.endswith(".ts"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Koa routes (often used with router)."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # router.get('/users', ...)
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                # router.method
                pattern = rf"router\.{method}\(['\"]([^'\"]+)['\"]"
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
                
                # app.method
                pattern = rf"app\.{method}\(['\"]([^'\"]+)['\"]"
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
