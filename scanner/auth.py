"""Authentication detection for API security schemes"""

import re
import os


class AuthDetector:
    """Detect authentication mechanisms in API code."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.security_schemes = {}
        self.protected_routes = []
    
    def scan(self):
        """Scan for authentication patterns."""
        for root, dirs, files in os.walk(self.project_path):
            # Skip virtual environments
            dirs[:] = [d for d in dirs if d not in ["venv", "env", "__pycache__"]]
            
            for file in files:
                if file.endswith(".py") or file.endswith(".js"):
                    self._scan_file(os.path.join(root, file))
        
        return {
            "schemes": self.security_schemes,
            "protected_routes": self.protected_routes
        }
    
    def _scan_file(self, filepath):
        """Detect authentication in file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            self._detect_jwt(content, filepath)
            self._detect_oauth2(content, filepath)
            self._detect_api_key(content, filepath)
            self._detect_basic_auth(content, filepath)
            
        except Exception:
            pass
    
    def _detect_jwt(self, content, filepath):
        """Detect JWT authentication."""
        jwt_patterns = [
            r"jwt\.decode",
            r"create_access_token",
            r"JWTManager",
            r"@jwt_required",
            r"@jwt_token_verified",
            r"from\s+flask_jwt_extended",
            r"from\s+pyjwt",
        ]
        
        for pattern in jwt_patterns:
            if re.search(pattern, content):
                self.security_schemes["jwt"] = {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JSON Web Token authentication"
                }
                break
        
        # Find JWT protected routes
        jwt_route_pattern = r"@(?:jwt_required|jwt_token_verified|token_required)"
        if re.search(jwt_route_pattern, content):
            self.protected_routes.append({
                "auth": "jwt",
                "file": os.path.basename(filepath)
            })
    
    def _detect_oauth2(self, content, filepath):
        """Detect OAuth2 authentication."""
        oauth_patterns = [
            r"OAuth2PasswordRequestForm",
            r"@oauth2_scheme",
            r"from\s+fastapi\.security\.oauth2",
            r"from\s+flask_oauthlib",
            r"GoogleOAuth2",
        ]
        
        for pattern in oauth_patterns:
            if re.search(pattern, content):
                self.security_schemes["oauth2"] = {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "scopes": {},
                            "tokenUrl": "token"
                        }
                    },
                    "description": "OAuth2 authentication"
                }
                break
    
    def _detect_api_key(self, content, filepath):
        """Detect API Key authentication."""
        api_key_patterns = [
            r"APIKeyHeader",
            r"APIKeyQuery",
            r"@api_key",
            r"x-api-key",
            r"from\s+fastapi\.security\.api_key",
        ]
        
        for pattern in api_key_patterns:
            if re.search(pattern, content):
                # Check if header or query
                if "Header" in pattern or "header" in content:
                    self.security_schemes["apiKeyHeader"] = {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                        "description": "API key in header"
                    }
                else:
                    self.security_schemes["apiKey"] = {
                        "type": "apiKey",
                        "in": "query",
                        "name": "api_key",
                        "description": "API key in query parameter"
                    }
                break
    
    def _detect_basic_auth(self, content, filepath):
        """Detect Basic authentication."""
        basic_patterns = [
            r"BasicAuth",
            r"HTTPBasicAuth",
            r"@basic_auth",
            r"from\s+fastapi\.security\.http",
        ]
        
        for pattern in basic_patterns:
            if re.search(pattern, content):
                self.security_schemes["basicAuth"] = {
                    "type": "http",
                    "scheme": "basic",
                    "description": "Basic authentication"
                }
                break
    
    def get_openapi_security(self):
        """Generate OpenAPI security schemes."""
        return self.security_schemes
