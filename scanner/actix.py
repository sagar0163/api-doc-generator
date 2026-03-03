"""Actix-web scanner - Detect endpoints in Rust Actix-web applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class ActixScanner(APIScanner):
    """Scan Actix-web projects for API endpoints."""
    
    def scan(self):
        """Scan Actix-web routes."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["target", ".git"]]
            
            for file in files:
                if file.endswith(".rs"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Actix-web routes."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # .route("/users", get(get_users))
            methods = ["get", "post", "put", "delete", "patch"]
            
            for method in methods:
                # HttpServer::new(|| App::new().route(...)
                pattern = rf'\.{method}\(["\']([^"\']+)["\'],\s*\w+\)'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # #[get("/users")]
            get_attr_pattern = r'#\[(get|post|put|delete|patch)\(["\']([^"\']+)["\']\]'
            matches = re.finditer(get_attr_pattern, content)
            
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                endpoint = Endpoint(path, method, filepath)
                self.endpoints.append(endpoint)
            
            # .service(web::resource("/users"))
            resource_pattern = r'web::resource\(["\']([^"\']+)["\']'
            matches = re.finditer(resource_pattern, content)
            
            for match in matches:
                path = match.group(1)
                endpoint = Endpoint(path, "RESOURCE", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
