"""Django REST Framework scanner - Enhanced Django API detection"""

import re
import os
from scanner.base import APIScanner, Endpoint


class DRFScanner(APIScanner):
    """Scan Django REST Framework projects for API endpoints."""
    
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
            
            # @action(detail=False, methods=['get']) and @api_view([...]) both
            # resolve to URLs only through the router; emit no fabricated
            # paths here (the django scanner resolves them from urls.py).
                        
        except Exception:
            pass
