"""Symfony scanner - Detect endpoints in Symfony PHP applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class SymfonyScanner(APIScanner):
    """Scan Symfony projects for API endpoints."""
    
    def scan(self):
        """Scan Symfony controllers."""
        # Scan src/Controller
        controller_dir = os.path.join(self.project_path, "src", "Controller")
        if os.path.exists(controller_dir):
            for root, dirs, files in os.walk(controller_dir):
                for file in files:
                    if file.endswith(".php"):
                        self._scan_file(os.path.join(root, file))
        
        # Scan config/routes
        routes_dir = os.path.join(self.project_path, "config", "routes")
        if os.path.exists(routes_dir):
            for root, dirs, files in os.walk(routes_dir):
                for file in files:
                    if file.endswith((".yaml", ".yml", ".php")):
                        self._scan_routes(os.path.join(root, file))
        
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract from controller files."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # #[Route('/api/users', methods: ['GET'])]
            route_pattern = r'#\[Route\(["\']([^"\']+)["\'](?:,\s*methods:\s*\[[^\]]+\])?'
            matches = re.finditer(route_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
    
    def _scan_routes(self, filepath):
        """Extract from route configuration."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # path: /api/users
            path_pattern = r"path:\s*['\"]([^'\"]+)['\"]"
            matches = re.finditer(path_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
