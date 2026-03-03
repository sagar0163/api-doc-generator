"""Sinatra scanner - Detect endpoints in Ruby Sinatra applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class SinatraScanner(APIScanner):
    """Scan Sinatra projects for API endpoints."""
    
    def scan(self):
        """Scan Sinatra routes."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in [".git", "vendor"]]
            
            for file in files:
                if file.endswith(".rb"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Sinatra routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # get '/users' do ... end
            methods = ["get", "post", "put", "delete", "patch", "options", "head"]
            
            for method in methods:
                pattern = rf'{method}\s+["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
