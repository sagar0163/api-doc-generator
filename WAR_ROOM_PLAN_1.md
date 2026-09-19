# WAR ROOM PLAN - Issue #1

Status of prior attempt (commits 455746f + 4be6697): pyproject.toml, apidocgen package
(cli.py, serve.py), fixed requirements.txt, thin main.py/serve.py wrappers, and a
working `pip install -e .` are already committed and verified. Remaining work:

- [x] Add `pyproject.toml` with `apidocgen` console-script entry point
- [x] Implement `apidocgen generate` and `apidocgen serve` subcommands (with
      `-o/--output`, `--format json|yaml`, `--title`, `--version`, `--framework`)
- [x] Fix `requirements.txt` (remove self-referential `api-doc-generator` line)
- [x] Keep `python main.py <path>` working as thin wrapper; keep `serve.py` working
- [x] Wire existing `to_yaml` into `--format yaml`
- [x] Fix Swagger UI index so it loads the actual spec file (works for JSON and YAML)
- [x] Add CLI tests (generate json/yaml, help text) under tests/
- [x] Re-verify clean-venv `pip install -e .` in this environment
- [x] Verify existing CI import checks still pass
- [x] Clean up build/test artifacts (__pycache__, egg-info, venv/, junk txt/x) + .gitignore
- [x] Run pytest, delete this plan file, final commit, push branch