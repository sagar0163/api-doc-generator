"""FastAPI scanner - Detect endpoints in FastAPI applications using AST"""

import os
import ast
import re
from scanner.base import APIScanner, Endpoint
from scanner.type_hints import TypeHintExtractor

class FastAPIScanner(APIScanner):
    """Scan FastAPI projects for API endpoints using AST."""
    
    def __init__(self, project_path, ignore_dirs=None, include=None):
        super().__init__(project_path, ignore_dirs, include)
        self.schemas = {}
    
    def scan(self):
        """Scan directory for FastAPI routes."""
        type_extractor = TypeHintExtractor(self.project_path)
        type_extractor.scan()
        self.schemas = type_extractor.get_openapi_types()

        for filepath in self._walk({".py"}):
            self._scan_file(filepath)
        return self.endpoints
    
    def _scan_file(self, filepath):
        """Extract FastAPI routes from Python file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return

        methods = ["get", "post", "put", "delete", "patch"]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # check @app.get("/path")
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr in methods:
                            method = decorator.func.attr.upper()
                            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                path = decorator.args[0].value
                                self._add_endpoint(path, method, filepath, node)
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        pass

    def _add_endpoint(self, path, method, filepath, node):
        endpoint = Endpoint(path, method, filepath)
        
        # Infer parameters from path
        path_params = re.findall(r'\{([^}]+)\}', path)
        for p in path_params:
            endpoint.parameters.append({
                "name": p,
                "in": "path",
                "required": True,
                "schema": {"type": "string"} # We could refine this using type hints
            })
            
        # Parse arguments for query/body params
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name in path_params:
                continue
            
            # Very simplistic: if it has an annotation, it's a query or body param
            # In real FastAPI, Pydantic models are request bodies, primitive types are query params
            param_type = {"type": "string"}
            is_body = False
            
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    type_name = arg.annotation.id
                    if type_name in ['int', 'str', 'float', 'bool']:
                        if type_name == 'int': param_type = {"type": "integer"}
                        elif type_name == 'float': param_type = {"type": "number"}
                        elif type_name == 'bool': param_type = {"type": "boolean"}
                    else:
                        is_body = True
                        param_type = {"$ref": f"#/components/schemas/{type_name}"}

            if is_body:
                endpoint.requestBody = {
                    "content": {
                        "application/json": {
                            "schema": param_type
                        }
                    },
                    "required": True
                }
            else:
                endpoint.parameters.append({
                    "name": arg_name,
                    "in": "query",
                    "required": False,
                    "schema": param_type
                })
                
        # Return type
        if node.returns:
            if isinstance(node.returns, ast.Name):
                type_name = node.returns.id
                if type_name in ['int', 'str', 'float', 'bool']:
                    if type_name == 'int': ret_type = {"type": "integer"}
                    elif type_name == 'float': ret_type = {"type": "number"}
                    elif type_name == 'bool': ret_type = {"type": "boolean"}
                    else: ret_type = {"type": "string"}
                else:
                    ret_type = {"$ref": f"#/components/schemas/{type_name}"}
                
                endpoint.responses = {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": ret_type
                            }
                        }
                    }
                }

        self.endpoints.append(endpoint)
