"""Hapi scanner - Detect endpoints in Hapi.js applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class HapiScanner(APIScanner):
    """Scan Hapi.js projects for API endpoints."""
    
    def scan(self):
        """Scan Hapi routes."""
        for filepath in self._walk({".js", ".ts"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Hapi routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # server.route({ method: 'GET', path: '/users' ... })
            # or routes: [{ method: 'GET', path: '/users' }]
            
            # method: 'get', path: '/users'
            method_pattern = r"method:\s*['\"](\w+)['\"]"
            path_pattern = r"path:\s*['\"]([^'\"]+)['\"]"
            
            method_matches = list(re.finditer(method_pattern, content))
            path_matches = list(re.finditer(path_pattern, content))
            
            for i, path_match in enumerate(path_matches):
                path = path_match.group(1)
                if i < len(method_matches):
                    method = method_matches[i].group(1).upper()
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
            
            # Shorthand: server.get('/users', ...)
            methods = ["get", "post", "put", "delete", "patch", "options"]
            
            for method in methods:
                pattern = rf"server\.{method}\(['\"]([^'\"]+)['\"]"
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
