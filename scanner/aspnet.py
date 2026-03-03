"""ASP.NET Core scanner - Detect endpoints in C# .NET applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class AspNetScanner(APIScanner):
    """Scan ASP.NET Core projects for API endpoints."""
    
    def scan(self):
        """Scan .NET controllers."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["bin", "obj", ".git"]]
            
            for file in files:
                if file.endswith(".cs"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract endpoints from C# files."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find [HttpGet], [HttpPost], etc.
            methods = {
                "HttpGet": "GET",
                "HttpPost": "POST",
                "HttpPut": "PUT",
                "HttpDelete": "DELETE",
                "HttpPatch": "PATCH"
            }
            
            for attribute, method in methods.items():
                # [HttpGet("/api/users")]
                pattern = rf'\[{attribute}\(?["\']([^"\']+)["\']?'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1) if match.group(1) else "/"
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
            
            # Route attributes
            # [Route("api/[controller]")]
            route_pattern = r'\[Route\(["\']([^"\']+)["\']'
            matches = re.finditer(route_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
