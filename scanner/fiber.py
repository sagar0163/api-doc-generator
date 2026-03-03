"""Fiber scanner - Detect endpoints in Go Fiber framework"""

import re
import os
from scanner.base import APIScanner, Endpoint


class FiberScanner(APIScanner):
    """Scan Go Fiber projects for API endpoints."""
    
    def scan(self):
        """Scan Fiber routes."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["vendor", "node_modules", ".git"]]
            
            for file in files:
                if file.endswith(".go"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Fiber routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # app.Get, app.Post, app.Put, app.Delete
            methods = ["Get", "Post", "Put", "Delete", "Patch", "Options", "Head"]
            
            for method in methods:
                pattern = rf'app\.{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # app.Group
            group_pattern = r'app\.Group\(["\']([^"\']+)["\']'
            matches = re.finditer(group_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GROUP", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
