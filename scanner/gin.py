"""Go Gin scanner - Detect endpoints in Go Gin applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class GinScanner(APIScanner):
    """Scan Go Gin projects for API endpoints."""
    
    def scan(self):
        """Scan directory for Gin routes."""
        for root, dirs, files in os.walk(self.project_path):
            # Skip vendor and test files
            if "vendor" in root or "_test.go" in root:
                continue
                
            for file in files:
                if file.endswith(".go"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Gin routes from Go file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find r.GET(), r.POST(), etc.
            methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
            
            for method in methods:
                # Pattern: r.GET("/", handler)
                pattern = rf'r\.{method}\(["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
            
            # Find group routes
            # Pattern: v1 := r.Group("/api/v1")
            group_pattern = r'r\.Group\(["\']([^"\']+)["\']\)'
            matches = re.finditer(group_pattern, content)
            
            for match in matches:
                group = match.group(1)
                # Look for routes within this group
                sub_pattern = rf'{group}(["\'][^"\']+["\'])'
                
        except Exception:
            pass
