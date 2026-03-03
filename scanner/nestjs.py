"""NestJS scanner - Detect endpoints in NestJS TypeScript applications"""

import re
import os
from scanner.base import APIScanner, Endpoint


class NestJSScanner(APIScanner):
    """Scan NestJS projects for API endpoints."""
    
    def scan(self):
        """Scan NestJS controllers."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "dist"]]
            
            for file in files:
                if file.endswith(".ts"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract NestJS decorators."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # @Get('users'), @Post('users'), etc.
            methods = ["Get", "Post", "Put", "Delete", "Patch", "Options", "Head"]
            
            for method in methods:
                pattern = rf'@{method}\(?["\']([^"\']+)["\']?'
                matches = re.finditer(pattern, content)
                
                for match in matches:
                    path = match.group(1) if match.group(1) else "/"
                    endpoint = Endpoint(path, method.upper(), filepath)
                    self.endpoints.append(endpoint)
            
            # @Controller('users')
            controller_pattern = r'@Controller\(["\']([^"\']+)["\']'
            matches = re.finditer(controller_pattern, content)
            
            controller_prefix = ""
            for match in matches:
                controller_prefix = match.group(1)
            
            # Update existing endpoints with controller prefix
            for ep in self.endpoints:
                if ep.path and not ep.path.startswith("/"):
                    ep.path = f"/{controller_prefix}/{ep.path}"
                    
        except Exception:
            pass
