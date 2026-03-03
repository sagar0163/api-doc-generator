"""Rocket scanner - Rust Rocket framework"""
import re, os
from scanner.base import APIScanner, Endpoint

class RocketScanner(APIScanner):
    def scan(self):
        for root, dirs, files in os.walk(self.project_path):
            for f in files:
                if f.endswith(".rs"):
                    self._scan_file(os.path.join(root, f))
        return self.endpoints
    
    def _scan_file(self, fp):
        try:
            with open(fp) as f:
                for m in re.finditer(r'#\[(\w+)\(["\']([^"\']+)["\']\]', f.read()):
                    ep = Endpoint(m.group(2), m.group(1).upper(), fp)
                    self.endpoints.append(ep)
        except: pass
