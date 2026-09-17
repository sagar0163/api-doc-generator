# WAR ROOM PLAN — Issue #5

## Status: Continuing from prior attempt (f21948f)

## Assessment of existing work
- [x] `action.yml` exists with composite runner, inputs (source-dir, config, output, fail-on-drift), branding
- [x] `.github/workflows/docs.yml` — push-to-main generates+commits, PR checks drift, test job runs pytest
- [x] `.github/workflows/test.yml` — runs pytest suite (not just imports)
- [x] `apidocgen check` subcommand implemented in main.py
- [x] `tests/test_check.py` — drift tests pass
- [x] `README.md` — has badge and 3-line action snippet
- [x] All 24 tests pass

## Remaining work
- [x] Improve error message in `run_check` to clearly say "docs are stale" + pointing at `apidocgen generate` per AC
- [x] Enhance `test_stale_docs_fail_with_actionable_message` to actually assert the error message content (name says "actionable message" but only checks return code)
- [ ] Validate `action.yml` structure (ensure `if` expressions, inputs, composite steps are correct)
- [ ] Verify `docs.yml` workflow structure is fully correct (permissions, job dependencies, paths)
- [ ] Ensure README has clear 3-line installation snippet with action usage
- [ ] Final review pass and commit
