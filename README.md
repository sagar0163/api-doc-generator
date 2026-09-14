# apidocgen

[![docs-fresh](https://img.shields.io/badge/docs-fresh-brightgreen.svg)]()
[![build](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![PyPI](https://img.shields.io/pypi/v/apidocgen.svg)]()

**A tool that automatically scans your codebase, detects the web frameworks in use, and generates deterministic OpenAPI documentation.**

## Why apidocgen?

- **Deterministic Spine**: Guaranteed structural mapping directly from your framework routes; no hallucinated endpoints.
- **Drift-Checked Docs**: Your spec is generated from code. Run it in CI to ensure docs are always in sync with implementation.
- **Self-Contained HTML**: Export a single, dependency-free `apidocgen export --html` page — Swagger UI CSS/JS and your spec are all inlined, so it renders offline (perfect for emailing, embedding, or committing to git).
- **Optional AI**: (Planned) Augment the structural backbone with LLM-generated descriptions, not hallucinated structure.

## Quickstart

1. **Install**
   ```bash
   pip install apidocgen
   ```
2. **Generate**
   ```bash
   apidocgen /path/to/project
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
| gin_enhanced | Go | supported |

## Advanced Usage

Force a specific scanner or define custom configuration via `api-doc.yaml`.

```bash
apidocgen /path/to/project --config api-doc.yaml
apidocgen /path/to/project --framework nestjs
apidocgen /path/to/project -o api-docs.yaml
```

### Interactive, offline HTML export

```bash
# One file you can open, email, or embed - no network needed
apidocgen export --html api-docs.html --spec api-docs.json --title "My API"
```

Everything is inlined into that single file: the Swagger UI CSS and JS bundle
(vendored under `vendor/swagger-ui-dist/`) and the OpenAPI spec itself (inline
SVG favicon too). Opening it makes **zero network requests** — no CDN scripts,
no external fonts. Optional extras:

```bash
apidocgen export --html api-docs.html --spec api-docs.json --title "My API" \
    --icon favicon.png --timestamp        # embed a favicon + "generated at" stamp
```

### Live preview (no CDN references either)

```bash
apidocgen serve --spec api-docs.json --port 8000
# Swagger UI: http://127.0.0.1:8000/docs   Raw spec: http://127.0.0.1:8000/openapi.json
```

`serve` serves the same standalone page: the HTML served to the browser has
Swagger UI fully inlined (no CDN references), so previewing offline works the
same way as the exported artifact.

#### Artifact size

Inlining `swagger-ui-dist@5.17.14` inflates the output:
`swagger-ui-bundle.js` (~1.45 MB) + `swagger-ui.css` (~152 KB) are embedded,
so a small spec yields a ~1.6 MB HTML file. Size grows with the spec size
(the spec JSON is embedded as-is). ~1.6 MB is reasonable to share via git or
email; the file is plain text and compresses well too.

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