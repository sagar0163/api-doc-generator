"""Flask scanner - Detect endpoints in Flask applications using AST"""

import os
import ast
import re
from scanner.base import APIScanner, Endpoint

class FlaskScanner(APIScanner):
    """Scan Flask projects for API endpoints using AST."""
    
    def scan(self):
        """Scan directory for Flask routes."""
        for filepath in self._walk({".py"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract Flask routes from Python file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return
            
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # check @app.route or @bp.route
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == 'route':
                            path = ""
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                path = decorator.args[0].value
                            
                            methods = ["GET"]
                            for kw in decorator.keywords:
                                if kw.arg == 'methods':
                                    if isinstance(kw.value, ast.List):
                                        methods = []
                                        for elt in kw.value.elts:
                                            if isinstance(elt, ast.Constant):
                                                methods.append(elt.value.upper())
                            
                            for method in methods:
                                endpoint = Endpoint(path, method, filepath)
                                
                                # parse path params like <int:user_id> or <user_id>
                                path_params = re.findall(r'<([^>:]+:)?([^>]+)>', path)
                                for t_prefix, p in path_params:
                                    p_type = "string"
                                    if t_prefix == 'int:': p_type = "integer"
                                    elif t_prefix == 'float:': p_type = "number"
                                    
                                    endpoint.parameters.append({
                                        "name": p,
                                        "in": "path",
                                        "required": True,
                                        "schema": {"type": p_type}
                                    })
                                    
                                # crude 404/error response inference
                                # "404/error responses are documented" from criteria
                                # we check if body returns a tuple ending in 404
                                has_404 = False
                                for child in ast.walk(node):
                                    if isinstance(child, ast.Return):
                                        if isinstance(child.value, ast.Tuple) and len(child.value.elts) > 1:
                                            last = child.value.elts[-1]
                                            if isinstance(last, ast.Constant) and last.value == 404:
                                                has_404 = True
                                
                                if has_404:
                                    endpoint.responses["404"] = {"description": "Not found"}
                                    
                                self.endpoints.append(endpoint)
