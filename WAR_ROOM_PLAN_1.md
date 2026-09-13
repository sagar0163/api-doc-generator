# WAR_ROOM_PLAN_1.md — Issue #1: pip-installable CLI with generate/serve subcommands

## Checklist

- [ ] Create `apidocgen/` package with `cli.py`: generate + serve subcommands, wire `to_yaml`, `--format json|yaml`, `--output/-o`, `--title`, `--version`, `--framework`
- [ ] Add `pyproject.toml` with `[project.scripts] apidocgen = "apidocgen.cli:main"` and package discovery for `apidocgen`, `scanner`, `generator`
- [ ] Fix `requirements.txt`: drop self-referential `api-doc-generator` line, keep only `PyYAML`
- [ ] Convert `main.py` into a thin backward-compatible wrapper (keeps `python main.py <path>` + `from main import detect_framework` for CI)
- [ ] Add `fixture/` Flask app so `apidocgen generate ./fixture -o out.yaml --format yaml` produces valid OpenAPI YAML; smoke-test serve on generated spec
- [ ] Verify: `pip install -e .` in clean venv, `apidocgen --help`, `apidocgen generate --help`, generate JSON+YAML, `requirements.txt` install, CI import checks
- [ ] Delete this plan file and make final commit, then push branch