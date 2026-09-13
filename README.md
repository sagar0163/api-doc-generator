# apidocgen

[![docs-fresh](https://img.shields.io/badge/docs-fresh-brightgreen.svg)]()
[![build](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![PyPI](https://img.shields.io/pypi/v/apidocgen.svg)]()

**A tool that automatically scans your codebase, detects the web frameworks in use, and generates deterministic OpenAPI documentation.**

## Why apidocgen?

- **Deterministic Spine**: Guaranteed structural mapping directly from your framework routes; no hallucinated endpoints.
- **Drift-Checked Docs**: Your spec is generated from code. Run it in CI to ensure docs are always in sync with implementation.
- **Self-Contained HTML**: Easily export out-of-the-box UI without complex toolchains.
- **Optional AI**: Augment the structural backbone with LLM-generated descriptions, not hallucinated structure.

## Quickstart

1. **Install**
   ```bash
   pip install apidocgen
   ```
2. **Generate**
   ```bash
   apidocgen generate /path/to/project
   ```
3. **View Docs**
   Open the generated `api-docs.json` (or `.yaml`) in Swagger UI or Redoc!

## Sample Output

```yaml
openapi: 3.0.0
info:
  title: API Documentation
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: Auto-detected GET route
      responses:
        '200':
          description: Successful response
```

## Supported Frameworks

Auto-detection currently supports the following frameworks. For a full breakdown of what is scanned (and upcoming stubs), see the [Detailed Supported Frameworks](docs/SUPPORTED_FRAMEWORKS.md) guide.

| Framework | Language | Status |
|-----------|----------|--------|
| flask | Python | supported |
| fastapi | Python | supported |
| django | Python | supported |
| drf | Python | supported |
| flask_restful | Python | supported |
| express | JavaScript | supported |
| koa | JavaScript | supported |
| hapi | JavaScript | supported |
| sails | JavaScript | supported |
| adonis | JavaScript | supported |
| nestjs | TypeScript | supported |
| laravel | PHP | supported |
| symfony | PHP | supported |
| codeigniter | PHP | supported |
| rails | Ruby | supported |
| sinatra | Ruby | supported |
| phoenix | Elixir | supported |
| play | Scala | supported |
| gin | Go | supported |
| echo | Go | supported |
| fiber | Go | supported |
| spring | Java | supported |
| ktor | Kotlin | supported |
| aspnet | C# | supported |
| actix | Rust | supported |
| rocket | Rust | supported |
| vapor | Swift | supported |

## Advanced Usage

Force a specific scanner or define custom configuration via `api-doc.yaml`.

```bash
apidocgen generate /path/to/project --config api-doc.yaml
apidocgen generate /path/to/project --framework nestjs
apidocgen generate /path/to/project -o api-docs.yaml
```

**`api-doc.yaml` Example:**
```yaml
framework: auto
include: []
ignore:
  - node_modules
  - venv
output: api-docs.json
server:
  url: http://localhost:3000
```

## Development & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a new framework scanner, fixture expectations, and our git-commit style guide.

**TODOs:**
- AI description augmentation hook
- Native self-contained HTML export command