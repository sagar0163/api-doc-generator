"""Echo scanner - Detect endpoints in Go Echo framework"""

import re
import os
from scanner.base import APIScanner, Endpoint


class EchoScanner(APIScanner):
    """Scan Go Echo projects for API endpoints."""
    
    def scan(self):
        """Scan Echo routes."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["vendor", "node_modules", ".git"]]
            
            for file in files:
                if file.endswith(".go"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Echo routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # e.GET, e.POST, e.PUT, e.DELETE
            methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
            
            for method in methods:
                pattern = rf'e\.{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
            
            # e.Group
            group_pattern = r'e\.Group\(["\']([^"\']+)["\']'
            matches = re.finditer(group_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GROUP", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
