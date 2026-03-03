"""Django scanner - Detect endpoints in Django applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class DjangoScanner(APIScanner):
    """Scan Django projects for API endpoints."""
    
    def scan(self):
        """Scan directory for Django views."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv", "env"]]
            
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Django URL patterns."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find path() and re_path()
            # path('admin/', admin.site.urls)
            path_pattern = r"path\(['\"]([^'\"]+)['\"]"
            matches = re.finditer(path_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GET", filepath)
                self.endpoints.append(endpoint)
            
            # Find @api_view
            api_view_pattern = r"@api_view\(['\"](\w+)['\"]\)"
            matches = re.finditer(api_view_pattern, content)
            
            for match in matches:
                method = match.group(1)
                endpoint = Endpoint("dynamic", method, filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
