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
- **Deterministic output** - identical inputs always produce byte-identical
  files, so specs are safe to commit and diff in CI
- **Drift detection** - `apidocgen check`/`diff` and
  `generate --fail-on-drift` fail the build when the committed spec goes
  stale, keeping docs in sync with the code (docs that never go stale)
- Configurable noise suppression via `drift.ignore`
- Stub "placeholder" scanners are clearly listed and excluded from
  auto-detection (they can never silently generate garbage)

## Install

```bash
pip install -r requirements.txt   # pyyaml
```

## Usage

```bash
./apidocgen /path/to/project                # write api-docs.json (legacy form)
./apidocgen generate /path/to/project       # same, explicit subcommand
./apidocgen generate /path/to/project --config api-doc.yaml
./apidocgen generate /path/to/project --framework nestjs
./apidocgen generate /path/to/project -o api-docs.yaml
./apidocgen check /path/to/project          # exit 1 on drift, 0 if up-to-date
./apidocgen diff /path/to/project           # print the additive->deleted list
./apidocgen frameworks --list              # supported vs placeholder scanners
```

`main.py` is also directly runnable: `python main.py /path/to/project`.

### Keeping docs in sync: `check`, `diff`, `--fail-on-drift`

The generated spec is committed to the repo. Whenever the codebase changes,
the committed spec drifts from what `generate` would produce. Two commands
make that visible and CI-safe:

- **`apidocgen check <path>`** regenerates the spec **in memory** and compares
  it to the committed file. It exits `0` with `No drift detected.` when they
  match, or prints a concise path-level report and exits `1` when they differ:

  ```
  $ apidocgen check .
  Scan the project...
  Drift detected: 2 path-level, 0 item-level change(s)
    - /archive/ (removed)
    + /users/{id} (added)
  ```

- **`apidocgen diff <path>`** prints the same comparison at full detail -
  path-level changes first, then item-level (method/param/schema) changes
  under each changed path:

  ```
  $ apidocgen diff .
  Drift detected: 2 path-level, 1 item-level change(s)
    ~ /users/ (changed)
        ~ get.parameters[0].name: id -> userId
    + /users/{id} (added)
  ```

  Both commands honor `check.mode` (below) and exit `0` when nothing drifted,
  so `check` is the CI gate and `diff` is the human-readable detail behind it.

- **`generate --fail-on-drift`** makes `generate` itself act as the gate: it
  regenerates, compares against the committed file **before** writing, and - if
  the committed spec is stale - prints the drift report, leaves the file
  untouched, and exits `1`. This is the "run `generate` in CI, get a failing
  build when docs are stale" flow:

  ```yaml
  # .github/workflows/docs.yml
  steps:
    - uses: actions/checkout@v4
    - run: pip install -r requirements.txt
    - run: ./apidocgen generate . --fail-on-drift
      # fails with exit 1 + a change list if the spec on disk is stale
  ```

  When a stale spec is detected, refresh it locally with plain
  `./apidocgen generate .`, review the diff, and commit the updated spec.

- **`check.mode: warn`** (config) flips `check`/`diff` into advisory mode:
  the drift report is still printed, but the exit code stays `0`. Useful
  pre-adoption, when a spec already drifted and you want to surface the diff
  without breaking builds. Pass `--fail-on-drift` to force a hard failure
  even in warn mode.

### Ignoring noise: `drift.ignore`

Enrichment and hand-maintained fields can differ between the committed spec
and a fresh run without meaning the docs are "stale". List their dot-paths in
`drift.ignore` so they never trip the gate:

```yaml
check:
  mode: fail        # fail = exit 1 on drift (default); warn = print only

drift:
  ignore:
    - info.description   # hand-maintained
    - "**.example"       # example values change without real drift
```

Patterns support `*` (one dot-segment) and `**` (any number of segments).
Ignored paths are pruned before comparison, so genuinely new endpoints,
renamed paths, and schema changes still surface.

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
check:
  mode: fail                 # fail (default) | warn seen above
drift:
  ignore:                    # dot-paths that never count as drift
    - info.description
    - "**.example"
```

CLI flags (`--config`, `--framework`, `-o`, `--fail-on-drift`) override
config values; config values override defaults.

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