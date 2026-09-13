"""Express scanner - Detect endpoints in Express.js applications"""

import re
import os
import json
from scanner.base import APIScanner, Endpoint


class ExpressScanner(APIScanner):
    """Scan Express.js projects for API endpoints."""
    
    def scan(self):
        """Scan directory for Express routes."""
        # _walk() already prunes node_modules/dist/etc.
        for filepath in self._walk({".js", ".ts"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Express routes from JavaScript/TypeScript file."""
        with open(filepath, "r") as f:
            content = f.read()
        
        # Find router.get(), router.post(), etc.
        methods = ["get", "post", "put", "delete", "patch", "options", "head"]
        
        for method in methods:
            # Pattern for router.method()
            pattern = rf"(?:router|app)\.{method}\(['\"]([^'\"]+)['\"]"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, method.upper(), filepath)
                self.endpoints.append(endpoint)
        
        # Find app.use() for middleware
        use_pattern = r"app\.use\(['\"]([^'\"]+)['\"]"
        matches = re.finditer(use_pattern, content)
        
        for match in matches:
            path = match.group(1)
            endpoint = Endpoint(path, "USE", filepath)
            self.endpoints.append(endpoint)
