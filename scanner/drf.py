"""Django REST Framework scanner - Enhanced Django API detection"""

import re
import os
from scanner.base import APIScanner, Endpoint


class DRFScanner(APIScanner):
    """Scan Django REST Framework projects for API endpoints."""
    
    def scan(self):
        """Scan DRF viewsets and API views."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv", "env", "migrations"]]
            
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract DRF viewsets and views."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # class UserViewSet(viewsets.ModelViewSet):
            viewset_pattern = r"class\s+(\w+ViewSet|ViewSet)\(viewsets\.\w+\):"
            matches = re.finditer(viewset_pattern, content)
            
            for match in matches:
                viewset_name = match.group(1)
                # Standard DRF actions
                actions = ["list", "create", "retrieve", "update", "partial_update", "destroy"]
                for action in actions:
                    endpoint = Endpoint(f"/{viewset_name.lower().replace('viewset', '')}", "GET", filepath)
                    self.endpoints.append(endpoint)
            
            # class UserAPIView(APIView):
            apiview_pattern = r"class\s+(\w+APIView)\(APIView\):"
            matches = re.finditer(apiview_pattern, content)
            
            for match in matches:
                view_name = match.group(1)
                endpoint = Endpoint(f"/{view_name.lower().replace('apiview', '')}", "GET", filepath)
                self.endpoints.append(endpoint)
            
            # @action(detail=False, methods=['get'])
            action_pattern = r"@action\(.*?methods=\[([^\]]+)\]"
            matches = re.finditer(action_pattern, content)
            
            for match in matches:
                methods = match.group(1)
                endpoint = Endpoint("/custom-action", "GET", filepath)
                self.endpoints.append(endpoint)
            
            # @api_view(['GET', 'POST'])
            apiview_decorator = r"@api_view\(([^)]+)\)"
            matches = re.finditer(apiview_decorator, content)
            
            for match in matches:
                endpoint = Endpoint("/function-based", "GET", filepath)
                self.endpoints.append(endpoint)
                    
        except Exception:
            pass
