# API Documentation Generator

A tool that automatically scans your codebase, detects the web frameworks in
use, and generates OpenAPI/Swagger documentation.

## Features

- Auto-detect the framework(s) in a project (Flask, FastAPI, Django, DRF,
  Express, NestJS, Koa, Hapi, Laravel, Symfony, Rails, Gin, Echo, Fiber,
  Spring, ASP.NET, Actix, Rocket and more - see
  [Supported Frameworks](docs/SUPPORTED_FRAMEWORKS.md))
- Force a scanner with `--framework <id>` regardless of detection
- `ignore`/`include` globs and `server.url` via `api-doc.yaml` config
- Export to JSON/YAML
- Stub "placeholder" scanners are clearly listed and excluded from
  auto-detection (they can never silently generate garbage)

## Install

```bash
pip install -r requirements.txt   # pyyaml
```

## Usage

```bash
./apidocgen /path/to/project                # auto-detect + scan + write api-docs.json
./apidocgen /path/to/project --config api-doc.yaml
./apidocgen /path/to/project --framework nestjs
./apidocgen /path/to/project -o api-docs.yaml
./apidocgen frameworks --list              # supported vs placeholder scanners
```

`main.py` is also directly runnable: `python main.py /path/to/project`.

### Config (`api-doc.yaml`)

```yaml
framework: auto              # or a supported id (see `frameworks --list`)
include: []                  # globs; empty = everything (ignoring `ignore`)
ignore:                      # additive to built-in defaults
  - node_modules
  - venv
  - __pycache__
  - dist
  - .git
output: api-docs.json        # .json (default) or .yaml
server:
  url: http://localhost:3000
  description: Local development server
```

CLI flags (`--config`, `--framework`, `-o`) override config values; config
values override defaults.

### Framework list

`apidocgen frameworks --list` distinguishes **supported** scanners from
**placeholder** stubs:

- Supported: fully functional, used by auto-detect when detected.
- Placeholder: stub files only - excluded from auto-detect with a warning.

## Project layout

```
scanner/        per-framework endpoint scanners
  registry.py   framework metadata + detection (supported vs placeholder)
generator/      OpenAPI spec generation
config.py       api-doc.yaml/json loading
main.py         CLI
docs/SUPPORTED_FRAMEWORKS.md   framework matrix
```

## Tests

```bash
python -m unittest discover -s tests
```