"""Vapor scanner - Detect endpoints in Swift Vapor applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class VaporScanner(APIScanner):
    """Scan Vapor projects for API endpoints."""
    
    def scan(self):
        """Scan Vapor routes."""
        for filepath in self._walk({".swift"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Vapor routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # app.get("users", ...)
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                pattern = rf'app\.{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # router.get("users", ...)
            for method in methods:
                pattern = rf'router\.{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
