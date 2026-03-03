"""CodeIgniter scanner - Detect endpoints in PHP CodeIgniter applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class CodeIgniterScanner(APIScanner):
    """Scan CodeIgniter projects for API endpoints."""
    
    def scan(self):
        """Scan CodeIgniter controllers."""
        # Scan app/Controllers
        controllers_dir = os.path.join(self.project_path, "app", "Controllers")
        if os.path.exists(controllers_dir):
            for root, dirs, files in os.walk(controllers_dir):
                for file in files:
                    if file.endswith(".php"):
                        self._scan_file(os.path.join(root, file))
        
        # Also check application/controllers (older CI)
        old_controllers = os.path.join(self.project_path, "application", "controllers")
        if os.path.exists(old_controllers):
            for root, dirs, files in os.walk(old_controllers):
                for file in files:
                    if file.endswith(".php"):
                        self._scan_file(os.path.join(root, file))
        
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract from CodeIgniter controllers."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # function get_users() { ... } -> /users GET
            # function post_users() { ... } -> /users POST
            # Or: function users() with _remap
            
            # Check for RESTful style: method_verb
            rest_methods = ["get_", "post_", "put_", "delete_", "patch_"]
            
            for rest_method in rest_methods:
                pattern = rf"function\s+{rest_method}(\w+)\s*\("
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1).lower()
                    method = rest_method.replace("_", "").upper()
                    endpoint = Endpoint(f"/{path}", method, filepath)
                    self.endpoints.append(endpoint)
            
            # Standard function definitions
            func_pattern = r"function\s+(\w+)\s*\("
            matches = re.finditer(func_pattern, content)
            
            for match in matches:
                func_name = match.group(1)
                # Skip magic methods
                if not func_name.startswith("_"):
                    endpoint = Endpoint(f"/{func_name}", "GET", filepath)
                    self.endpoints.append(endpoint)
                    
        except Exception:
            pass
