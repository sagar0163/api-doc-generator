"""Django REST Framework scanner - Enhanced Django API detection using AST"""

import os
import ast
import re
from scanner.base import APIScanner, Endpoint

class DRFScanner(APIScanner):
    """Scan Django REST Framework projects for API endpoints using AST."""
    
    def scan(self):
        """Scan DRF viewsets and API views."""
        for filepath in self._walk({".py"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract DRF viewsets and views."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else '') for base in node.bases]
                
                # Check if it's a ViewSet
                is_viewset = any('ViewSet' in b for b in bases)
                is_apiview = any('APIView' in b for b in bases)
                
                if is_viewset:
                    viewset_name = node.name
                    path = f"/{viewset_name.lower().replace('viewset', '')}"
                    
                    actions = ["list", "create", "retrieve", "update", "partial_update", "destroy"]
                    for action in actions:
                        method = "GET"
                        if action == "create": method = "POST"
                        elif action in ["update", "partial_update"]: method = "PUT"
                        elif action == "destroy": method = "DELETE"
                        
                        endpoint = Endpoint(path, method, filepath)
                        
                        if action in ["retrieve", "update", "partial_update", "destroy"]:
                            endpoint.path = f"{path}/{{id}}"
                            endpoint.parameters.append({
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            })
                            
                        self.endpoints.append(endpoint)
                        
                elif is_apiview:
                    view_name = node.name
                    path = f"/{view_name.lower().replace('apiview', '')}"
                    endpoint = Endpoint(path, "GET", filepath)
                    self.endpoints.append(endpoint)
