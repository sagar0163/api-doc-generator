"""Ktor scanner - Detect endpoints in Kotlin Ktor applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class KtorScanner(APIScanner):
    """Scan Ktor projects for API endpoints."""
    
    def scan(self):
        """Scan Ktor routes."""
        for filepath in self._walk({".kt"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Ktor routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # get("/users", ...), post("/users", ...)
            methods = ["get", "post", "put", "delete", "patch", "options", "head"]
            
            for method in methods:
                pattern = rf'{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # route("/api") { ... }
            route_pattern = r'route\(["\']([^"\']+)["\']'
            matches = re.finditer(route_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "ROUTE", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
