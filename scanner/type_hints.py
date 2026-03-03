"""Type hint extraction for OpenAPI type mapping"""

import ast
import os
import re


class TypeHintExtractor:
    """Extract Python type hints and convert to OpenAPI types."""
    
    # Python type to OpenAPI type mapping
    TYPE_MAP = {
        "str": {"type": "string"},
        "int": {"type": "integer", "format": "int32"},
        "float": {"type": "number", "format": "float"},
        "bool": {"type": "boolean"},
        "list": {"type": "array"},
        "dict": {"type": "object"},
        "bytes": {"type": "string", "format": "binary"},
        "datetime": {"type": "string", "format": "date-time"},
        "date": {"type": "string", "format": "date"},
        "UUID": {"type": "string", "format": "uuid"},
        "EmailStr": {"type": "string", "format": "email"},
        "HttpUrl": {"type": "string", "format": "uri"},
    }
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.type_definitions = {}
    
    def scan(self):
        """Scan for type definitions."""
        for root, dirs, files in os.walk(self.project_path):
            # Skip virtual environments
            dirs[:] = [d for d in dirs if d not in ["venv", "env", "__pycache__", ".git"]]
            
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.type_definitions
    
    def _scan_file(self, filepath):
        """Extract type hints from Python file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Find function definitions with type hints
                if isinstance(node, ast.FunctionDef):
                    self._extract_function_types(node, filepath)
                    
                # Find class definitions (potential models)
                elif isinstance(node, ast.ClassDef):
                    self._extract_class_types(node, filepath)
                    
        except Exception:
            pass
    
    def _extract_function_types(self, func_node, filepath):
        """Extract types from function definition."""
        func_name = func_node.name
        
        # Extract return type
        if func_node.returns:
            return_type = self._type_to_openapi(func_node.returns)
            
            # Extract parameter types
            params = {}
            for arg in func_node.args.args:
                if arg.annotation:
                    param_type = self._type_to_openapi(arg.annotation)
                    params[arg.arg] = param_type
            
            self.type_definitions[func_name] = {
                "return_type": return_type,
                "parameters": params,
                "location": filepath
            }
    
    def _extract_class_types(self, class_node, filepath):
        """Extract types from class definition."""
        class_name = class_node.name
        
        fields = {}
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    field_name = node.target.id
                    if node.annotation:
                        field_type = self._type_to_openapi(node.annotation)
                        fields[field_name] = field_type
        
        if fields:
            self.type_definitions[class_name] = {
                "type": "object",
                "properties": fields,
                "location": filepath
            }
    
    def _type_to_openapi(self, type_node):
        """Convert Python type to OpenAPI schema."""
        if isinstance(type_node, ast.Name):
            type_name = type_node.id
            
            if type_name in self.TYPE_MAP:
                return self.TYPE_MAP[type_name]
            
            # Custom type - reference it
            return {"$ref": f"#/components/schemas/{type_name}"}
        
        elif isinstance(type_node, ast.Subscript):
            # Handle List[T], Optional[T], etc.
            if isinstance(type_node.value, ast.Name):
                base_type = type_node.value.id
                
                if base_type == "List":
                    if type_node.slice:
                        return {"type": "array", "items": {"type": "string"}}
                    return {"type": "array"}
                
                elif base_type == "Optional":
                    if type_node.slice:
                        return self._type_to_openapi(type_node.slice)
                    return {"type": "string"}
                
                elif base_type == "Dict":
                    return {"type": "object"}
        
        return {"type": "string"}
    
    def get_openapi_types(self):
        """Generate OpenAPI components/schemas section."""
        schemas = {}
        
        for name, type_info in self.type_definitions.items():
            if isinstance(type_info, dict) and "type" in type_info:
                schemas[name] = type_info
        
        return schemas
