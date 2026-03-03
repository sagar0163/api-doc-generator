"""Main CLI tool for API Documentation Generator"""

import argparse
import os
import sys
from scanner.flask import FlaskScanner
from scanner.fastapi import FastAPIScanner
from scanner.express import ExpressScanner
from generator.openapi import OpenAPIGenerator


def detect_framework(project_path):
    """Auto-detect the framework used in the project."""
    
    # Check for Flask
    if os.path.exists(os.path.join(project_path, "app.py")):
        with open(os.path.join(project_path, "app.py"), "r") as f:
            if "from flask import" in f.read() or "Flask(" in f.read():
                return "flask"
    
    # Check for FastAPI
    if os.path.exists(os.path.join(project_path, "main.py")):
        with open(os.path.join(project_path, "main.py"), "r") as f:
            if "from fastapi import" in f.read() or "FastAPI(" in f.read():
                return "fastapi"
    
    # Check for Express
    if os.path.exists(os.path.join(project_path, "package.json")):
        with open(os.path.join(project_path, "package.json"), "r") as f:
            content = f.read()
            if '"express"' in content:
                return "express"
    
    return None


def scan_project(project_path, framework=None):
    """Scan project for API endpoints."""
    
    if framework is None:
        framework = detect_framework(project_path)
    
    if framework == "flask":
        scanner = FlaskScanner(project_path)
    elif framework == "fastapi":
        scanner = FastAPIScanner(project_path)
    elif framework == "express":
        scanner = ExpressScanner(project_path)
    else:
        # Try all scanners
        scanners = [
            FlaskScanner(project_path),
            FastAPIScanner(project_path),
            ExpressScanner(project_path)
        ]
        
        endpoints = []
        for s in scanners:
            s.scan()
            endpoints.extend(s.endpoints)
        
        return endpoints
    
    return scanner.scan()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="API Documentation Generator - Auto-scan projects and generate API specs"
    )
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("-f", "--framework", choices=["flask", "fastapi", "express"],
                       help="Framework type (auto-detect if not specified)")
    parser.add_argument("-o", "--output", default="api-docs.json",
                       help="Output file path")
    parser.add_argument("-t", "--title", default="My API",
                       help="API title")
    parser.add_argument("-v", "--version", default="1.0.0",
                       help="API version")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        sys.exit(1)
    
    print(f"Scanning {args.project_path} for API endpoints...")
    
    endpoints = scan_project(args.project_path, args.framework)
    
    print(f"Found {len(endpoints)} endpoints")
    
    # Generate OpenAPI spec
    generator = OpenAPIGenerator(title=args.title, version=args.version)
    
    for endpoint in endpoints:
        generator.add_endpoint(endpoint)
    
    # Write output
    output = generator.to_json()
    
    with open(args.output, "w") as f:
        f.write(output)
    
    print(f"API documentation generated: {args.output}")


if __name__ == "__main__":
    main()
