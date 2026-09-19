# API Documentation Generator

A tool that automatically scans your codebase and generates API specification
documentation (OpenAPI/Swagger).

## Features

- Auto-detect API endpoints
- Generate OpenAPI/Swagger specs
- Support for Python (Flask, FastAPI) and Node.js (Express)
- Export to JSON/YAML
- Serve specs with a local Swagger UI

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Generate a spec from a project directory
apidocgen generate ./my-project -o api-docs.json --format json
apidocgen generate ./my-project -o api-docs.yaml --format yaml --framework flask

# Serve a generated spec with Swagger UI
apidocgen serve --spec api-docs.yaml
```

### Options

- `generate`: `-o/--output`, `--format json|yaml`, `--title`, `--version`,
  `-f/--framework flask|fastapi|express`
- `serve`: `-s/--spec <file>`, `-p/--port <port>`

Backward compatibility: `python main.py <path>` still works.