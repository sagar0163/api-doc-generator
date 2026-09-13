"""Go Gin scanner - Detect endpoints in Go Gin applications"""

import re
from scanner.base import APIScanner, Endpoint


class GinScanner(APIScanner):
    """Scan Go Gin projects for API endpoints."""

    def scan(self):
        """Scan directory for Gin routes."""
        # Skip _test.go files: they reference handlers, not real routes.
        for filepath in self._walk({".go"}):
            if filepath.endswith("_test.go"):
                continue
            self._scan_file(filepath)
        return self.endpoints

    def _scan_file(self, filepath):
        """Extract Gin routes from a Go file."""
        try:
            with open(filepath, "r", errors="ignore") as f:
                content = f.read()
        except OSError:
            return

        # Group prefixes: v1 := r.Group("/api/v1")  ->  {v1: "/api/v1"}
        groups = {}
        for match in re.finditer(
            r'(\w+)\s*(?::=|=)\s*r\.Group\(["\']([^"\']+)["\']\)',
            content,
        ):
            groups[match.group(1)] = match.group(2)

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
        seen = set()

        for method in methods:
            # r.GET("/health", h)  or  v1.GET("/users", h)
            pattern = rf'(\w+)\.{method}\(["\']([^"\']+)["\']'
            for match in re.finditer(pattern, content):
                receiver, path = match.group(1), match.group(2)
                if receiver == "r":
                    prefix = ""
                elif receiver in groups:
                    prefix = groups[receiver]
                else:
                    # Unknown receiver - not a Gin route on our router.
                    continue
                full_path = prefix + path
                if full_path in seen:
                    continue
                seen.add(full_path)
                self.endpoints.append(Endpoint(full_path, method, filepath))