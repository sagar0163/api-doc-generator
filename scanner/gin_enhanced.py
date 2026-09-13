"""Gin scanner - Already exists, adding enhancement"""
# Enhanced Gin scanner with more patterns
import re
import os
from scanner.base import APIScanner, Endpoint

class GinEnhancedScanner(APIScanner):
    """Enhanced Gin scanner with middleware detection"""
    
    def scan(self):
        for filepath in self._walk({".go"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Enhanced pattern matching
            methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
            for method in methods:
                pattern = rf'r\.{method}\(["\']([^"\']+)["\']'
                for match in re.finditer(pattern, content):
                    ep = Endpoint(match.group(1), method, filepath)
                    self.endpoints.append(ep)
        except: pass
