# Issue #4: Drift detection (`check`/`diff`, deterministic output, `--fail-on-drift`)

Branch: `war-room-issue-4` (base `main`). One commit per checked box.

- [x] Make serialization deterministic: `sort_keys=True` in `generator/openapi.py` (JSON + YAML), trailing newline for JSON
- [ ] Config: add `check.mode: fail|warn` and `drift.ignore` defaults + merge/validation in `config.py`; document in `api-doc.yaml`
- [ ] New `drift.py`: `detect_drift()`, `remove_ignored()` (dot-paths with `*`/`**`), item-level `iter_item_changes()`, `render_drift()` report
- [ ] CLI: `generate`/`check`/`diff` subcommands in `main.py` (legacy positional scan preserved); `--fail-on-drift` gates `generate` exit code; `check` regenerates in-memory, exits 1 on drift unless `check.mode: warn`
- [ ] Tests (`tests/test_drift.py`) for all acceptance criteria: byte-identical consecutive runs; endpoint/path/schema drift flips `check` exit 1 + lists change; `diff` shows added/removed/changed ops; `--fail-on-drift` gating; `drift.ignore` suppression
- [ ] README: document `generate`/`check`/`diff`, `--fail-on-drift`, `drift.ignore`, local + CI examples
- [ ] Run full test suite (`python -m unittest discover -s tests`), fix failures
- [ ] Delete plan, final commit referencing #4, push branch