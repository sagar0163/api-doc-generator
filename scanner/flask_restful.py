"""Flask-RESTful scanner - Enhanced Flask API detection"""

import re
import os
from scanner.base import APIScanner, Endpoint


class FlaskRestfulScanner(APIScanner):
    """Scan Flask-RESTful projects for API endpoints."""
    
    def scan(self):
        """Scan Flask-RESTful resources."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv", "env"]]
            
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Flask-RESTful resources."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # class UserResource(Resource):
            resource_pattern = r"class\s+(\w+Resource)\(Resource\):"
            matches = re.finditer(resource_pattern, content)
            
            for match in matches:
                resource_name = match.group(1).replace("Resource", "").lower()
                
                # Check for method definitions in the class
                class_content = self._get_class_content(content, match.start())
                
                # def get(self): ...
                methods = ["get", "post", "put", "delete", "patch"]
                for method in methods:
                    if f"def {method}(self" in class_content:
                        endpoint = Endpoint(f"/{resource_name}", method.upper(), filepath)
                        self.endpoints.append(endpoint)
            
            # @marshal_with
            marshal_pattern = r"@marshal_with\(([^)]+)\)"
            matches = re.finditer(marshal_pattern, content)
            
            for match in matches:
                endpoint = Endpoint("/marshaled-endpoint", "GET", filepath)
                self.endpoints.append(endpoint)
            
            # @reqparse
            reqparse_pattern = r"@reqparse\."
            if re.search(reqparse_pattern, content):
                endpoint = Endpoint("/parsed-request", "POST", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
    
    def _get_class_content(self, content, class_start):
        """Get content between class definition and next class."""
        # Find next class or end of file
        next_class = re.search(r"\nclass ", content[class_start + 10:])
        
        if next_class:
            return content[class_start:class_start + next_class.start()]
        return content[class_start:]
