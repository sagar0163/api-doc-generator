"""Flask scanner - Detect endpoints in Flask applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class FlaskScanner(APIScanner):
    """Scan Flask projects for API endpoints."""
    
    def scan(self):
        """Scan directory for Flask routes."""
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Flask routes from Python file."""
        with open(filepath, "r") as f:
            content = f.read()
        
        # Find @app.route decorators
        route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?"
        matches = re.finditer(route_pattern, content)
        
        for match in matches:
            path = match.group(1)
            methods = match.group(2) or "GET"
            methods = [m.strip().strip("'\"") for m in methods.split(",")]
            
            endpoint = Endpoint(path, methods[0], filepath)
            self.endpoints.append(endpoint)
        
        # Find @bp.route decorators
        bp_pattern = r"@bp\.route\(['\"]([^'\"]+)['\"](?:,\s*methods=\[([^\]]+)\])?"
        bp_matches = re.finditer(bp_pattern, content)
        
        for match in bp_matches:
            path = match.group(1)
            methods = match.group(2) or "GET"
            methods = [m.strip().strip("'\"") for m in methods.split(",")]
            
            endpoint = Endpoint(path, methods[0], filepath)
            self.endpoints.append(endpoint)
