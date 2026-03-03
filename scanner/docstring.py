"""Docstring parser for generating OpenAPI descriptions"""

import re
import ast
import os


class DocstringParser:
    """Parse docstrings and convert to OpenAPI descriptions."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.docs = {}
    
    def scan(self):
        """Scan for docstrings."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in ["venv", "env", "__pycache__"]]
            
            for file in files:
                if file.endswith(".py"):
                    self._scan_file(os.path.join(root, file))
        return self.docs
    
    def _scan_file(self, filepath):
        """Extract docstrings from Python file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        self.docs[node.name] = self._parse_docstring(docstring, node)
                        
        except Exception:
            pass
    
    def _parse_docstring(self, docstring, func_node):
        """Parse docstring into structured format."""
        lines = docstring.split("\n")
        
        # First line is summary
        summary = lines[0].strip() if lines else ""
        
        # Parse parameters from Args section
        params = self._extract_params(lines)
        
        # Parse returns section
        returns = self._extract_returns(lines)
        
        return {
            "summary": summary,
            "description": "\n".join(lines[1:]).strip(),
            "parameters": params,
            "returns": returns,
            "location": func_node.lineno
        }
    
    def _extract_params(self, lines):
        """Extract parameter descriptions."""
        params = {}
        in_args = False
        
        for line in lines:
            if "Args:" in line or "Parameters:" in line:
                in_args = True
                continue
            
            if in_args:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    # Parse param: description
                    param_match = re.match(r"[\-\*]\s*(\w+):\s*(.+)", line.strip())
                    if param_match:
                        params[param_match.group(1)] = param_match.group(2).strip()
                elif line.strip() == "" or ":" not in line:
                    in_args = False
        
        return params
    
    def _extract_returns(self, lines):
        """Extract return value description."""
        in_returns = False
        returns = {}
        
        for line in lines:
            if "Returns:" in line or "Return:" in line:
                in_returns = True
                continue
            
            if in_returns:
                if ":" in line and not line.strip().startswith("-"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        returns["type"] = parts[0].strip()
                        returns["description"] = parts[1].strip()
                        break
                elif line.strip() == "":
                    in_returns = False
        
        return returns
    
    def to_openapi_params(self):
        """Convert to OpenAPI parameter format."""
        openapi_params = []
        
        for func_name, doc in self.docs.items():
            for param_name, description in doc.get("parameters", {}).openapi_params.append({
                "name": param_name,
                "in": "query",
                "description": description,
                "required": True
            })
        
        return openapi_params
