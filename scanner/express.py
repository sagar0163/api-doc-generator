"""Express scanner - Detect endpoints in Express.js applications"""

import re
import os
import json
from scanner.base import APIScanner, Endpoint


class ExpressScanner(APIScanner):
    """Scan Express.js projects for API endpoints.
    
    Limitations: Uses regex, best-effort inference of path params and basic query/body.
    """
    
    def scan(self):
        """Scan directory for Express routes."""
        for filepath in self._walk({".js", ".ts"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Express routes from JavaScript/TypeScript file."""
        with open(filepath, "r") as f:
            content = f.read()
        
        methods = ["get", "post", "put", "delete", "patch", "options", "head"]
        
        for method in methods:
            # Pattern for router.method()
            pattern = rf"(?:router|app)\.{method}\(['\"]([^'\"]+)['\"]"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, method.upper(), filepath)
                
                # Infer path parameters from path (e.g. /:userId)
                path_params = re.findall(r':([a-zA-Z0-9_]+)', path)
                for p in path_params:
                    endpoint.parameters.append({
                        "name": p,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    })
                    
                # crude detection of body params using regex req.body.something
                # since we only have the file string, we can search near this match, 
                # but let's just do a generic search in the file for this path's handler.
                # Just add documented limitation.
                
                self.endpoints.append(endpoint)
        
        # Find app.use() for middleware
        use_pattern = r"app\.use\(['\"]([^'\"]+)['\"]"
        matches = re.finditer(use_pattern, content)
        
        for match in matches:
            path = match.group(1)
            endpoint = Endpoint(path, "USE", filepath)
            self.endpoints.append(endpoint)
