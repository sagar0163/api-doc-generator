"""Java Spring Boot scanner - Detect endpoints in Spring Boot applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class SpringBootScanner(APIScanner):
    """Scan Spring Boot projects for API endpoints."""
    
    def scan(self):
        """Scan directory for Spring Boot controllers."""
        for root, dirs, files in os.walk(self.project_path):
            # Skip build directories
            if any(x in root for x in ["target", "build", ".gradle", "node_modules"]):
                continue
                
            for file in files:
                if file.endswith(".java"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Spring Boot routes from Java file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find @RequestMapping, @GetMapping, @PostMapping, etc.
            method_mapping = {
                "GetMapping": "GET",
                "PostMapping": "POST",
                "PutMapping": "PUT",
                "DeleteMapping": "DELETE",
                "PatchMapping": "PATCH",
                "RequestMapping": "GET"  # Default
            }
            
            for annotation, method in method_mapping.items():
                # Pattern: @GetMapping("/users")
                pattern = rf'@{annotation}\(?["\']([^"\']+)["\']'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1)
                    endpoint = Endpoint(path, method, filepath)
                    self.endpoints.append(endpoint)
                    
                    # Check for method specification
                    # @RequestMapping(value="/path", method=RequestMethod.GET)
                    method_spec = rf'@{annotation}\([^)]*method=RequestMethod\.([A-Z]+)'
                    method_matches = re.finditer(method_spec, content)
                    
                    for m in method_matches:
                        endpoint.method = m.group(1)
            
            # Find @RestController
            if "@RestController" in content or "@Controller" in content:
                pass
                
        except Exception:
            pass
