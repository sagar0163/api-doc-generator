"""Django scanner - Detect endpoints in Django applications"""

import re
from scanner.base import APIScanner, Endpoint


class DjangoScanner(APIScanner):
    """Scan Django projects for API endpoints."""

    def __init__(self, project_path, ignore_dirs=None):
        super().__init__(project_path, ignore_dirs=ignore_dirs)
        self._url_views = {}
        self._api_views = {}

    def _scan_file(self, filepath):
        """Extract Django URL patterns and @api_view views from one file."""
        try:
            with open(filepath, "r", errors="ignore") as f:
                content = f.read()
        except OSError:
            return

        # path('/users/', views.user_list)   ->  {view_name: route_path}
        for match in re.finditer(r"path\(['\"]([^'\"]+)['\"]\s*,\s*([\w.]+)", content):
            route_path, view = match.group(1), match.group(2)
            if "." in view:
                view = view.rsplit(".", 1)[1]
            # 'admin.site.urls' / include(...) are includes, not leaf views.
            if view in ("urls", "include"):
                continue
            self._url_views.setdefault(view, route_path)

        # @api_view(['GET', 'POST']) decorating a function below it.
        # The old single-string regex (@api_view('GET')) never matched the
        # standard list/tuple form, silently dropping these views.
        for match in re.finditer(
            r"@api_view\(([^)]+)\)\s*\n\s*def\s+(\w+)\s*\(",
            content,
        ):
            methods = re.findall(r"['\"](\w+)['\"]", match.group(1))
            if methods:
                self._api_views.setdefault(match.group(2), [m.upper() for m in methods])

    def finish(self):
        """Merge URL patterns with @api_view handlers across files."""
        seen = set()
        for route_path in sorted(set(self._url_views.values())):
            if route_path in seen:
                continue
            seen.add(route_path)
            self.endpoints.append(Endpoint(route_path, "GET", self.project_path))

        for view_name, methods in self._api_views.items():
            route_path = self._url_views.get(view_name)
            if not route_path:
                continue
            for method in methods:
                if (route_path, method) in seen:
                    continue
                seen.add((route_path, method))
                self.endpoints.append(Endpoint(route_path, method, self.project_path))

        return self.endpoints

    def scan(self):
        """Scan the project and merge URL + @api_view routes."""
        self._url_views = {}
        self._api_views = {}
        for filepath in self._walk({".py"}):
            self._scan_file(filepath)
        return self.finish()