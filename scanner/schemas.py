"""Advanced static analysis for Pydantic schemas"""

import re
import ast
import os


class PydanticSchemaExtractor:
    """Extract Pydantic model schemas from Python files."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.schemas = {}
    
    def scan(self):
        """Scan for Pydantic models."""
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.schemas
    
    def _scan_file(self, filepath):
        """Extract Pydantic models from file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find BaseModel inheritance
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            if base.id == "BaseModel":
                                schema = self._extract_model(node)
                                self.schemas[node.name] = schema
                                
        except Exception as e:
            pass
    
    def _extract_model(self, class_node):
        """Extract model fields and types."""
        fields = {}
        
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    field_name = node.target.id
                    
                    # Extract type hint
                    if isinstance(node.annotation, ast.Name):
                        field_type = node.annotation.id
                    elif isinstance(node.annotation, ast.Subscript):
                        field_type = self._get_subscript_type(node.annotation)
                    else:
                        field_type = "any"
                    
                    fields[field_name] = {"type": field_type}
        
        return {"fields": fields}
    
    def _get_subscript_type(self, node):
        """Get type from subscript (e.g., List[str])"""
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}[...]"
        return "any"


class MarshmallowSchemaExtractor:
    """Extract Marshmallow schemas from Python files."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.schemas = {}
    
    def scan(self):
        """Scan for Marshmallow schemas."""
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.schemas
    
    def _scan_file(self, filepath):
        """Extract Marshmallow schemas."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            # Find Schema inheritance
            schema_pattern = r"class (\w+)\(Schema\):"
            matches = re.finditer(schema_pattern, content)
            
            for match in matches:
                schema_name = match.group(1)
                self.schemas[schema_name] = {"name": schema_name}
                
        except Exception as e:
            pass


def extract_schemas(project_path):
    """Extract all schemas from project."""
    pydantic = PydanticSchemaExtractor(project_path)
    marshmallow = MarshmallowSchemaExtractor(project_path)
    
    return {
        "pydantic": pydantic.scan(),
        "marshmallow": marshmallow.scan()
    }
