"""Command-line interface for the API Documentation Generator."""

import argparse
import os
import sys

from scanner.flask import FlaskScanner
from scanner.fastapi import FastAPIScanner
from scanner.express import ExpressScanner
from generator.openapi import OpenAPIGenerator


def detect_framework(project_path):
    """Auto-detect the framework used in the project."""
    if os.path.exists(os.path.join(project_path, "app.py")):
        with open(os.path.join(project_path, "app.py"), "r") as f:
            if "from flask import" in f.read() or "Flask(" in f.read():
                return "flask"

    if os.path.exists(os.path.join(project_path, "main.py")):
        with open(os.path.join(project_path, "main.py"), "r") as f:
            if "from fastapi import" in f.read() or "FastAPI(" in f.read():
                return "fastapi"

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


def build_parser():
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="apidocgen",
        description="API Documentation Generator - Auto-scan projects and generate API specs"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser(
        "generate",
        help="Scan a project and generate an OpenAPI spec"
    )
    gen_parser.add_argument("project_path", help="Path to project directory")
    gen_parser.add_argument(
        "-f", "--framework",
        choices=["flask", "fastapi", "express"],
        help="Framework type (auto-detect if not specified)"
    )
    gen_parser.add_argument(
        "-o", "--output", default="api-docs.json",
        help="Output file path"
    )
    gen_parser.add_argument(
        "--format", choices=["json", "yaml"], default="json",
        help="Output format (default: json)"
    )
    gen_parser.add_argument(
        "-t", "--title", default="My API",
        help="API title"
    )
    gen_parser.add_argument(
        "-v", "--version", default="1.0.0",
        help="API version"
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve a generated OpenAPI spec with Swagger UI"
    )
    serve_parser.add_argument(
        "-p", "--port", type=int, default=8000,
        help="Port to serve on"
    )
    serve_parser.add_argument(
        "-s", "--spec", default="openapi.json",
        help="Path to OpenAPI spec"
    )

    return parser


def cmd_generate(args):
    """Handle the `generate` subcommand."""
    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        sys.exit(1)

    print(f"Scanning {args.project_path} for API endpoints...")

    endpoints = scan_project(args.project_path, args.framework)

    print(f"Found {len(endpoints)} endpoints")

    generator = OpenAPIGenerator(title=args.title, version=args.version)
    for endpoint in endpoints:
        generator.add_endpoint(endpoint)

    if args.format == "yaml":
        output = generator.to_yaml()
    else:
        output = generator.to_json()

    with open(args.output, "w") as f:
        f.write(output)

    print(f"API documentation generated: {args.output}")


def cmd_serve(args):
    """Handle the `serve` subcommand."""
    from apidocgen.serve import serve as run_server
    run_server(args.spec, args.port)


def main(argv=None):
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "serve":
        cmd_serve(args)


if __name__ == "__main__":
    main()