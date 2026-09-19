# WAR ROOM PLAN — Issue #5

## Status: Continuing from prior attempt (f21948f)

## Assessment of existing work
- [x] `action.yml` exists with composite runner, inputs (source-dir, config, output, fail-on-drift), branding
- [x] `.github/workflows/docs.yml` — push-to-main generates+commits, PR checks drift, test job runs pytest
- [x] `.github/workflows/test.yml` — runs pytest suite (not just imports)
- [x] `apidocgen check` subcommand implemented in main.py
- [x] `tests/test_check.py` — drift tests pass
- [x] `README.md` — has badge and action snippet
- [x] All tests pass

## Remaining work (current attempt)
- [x] Improve error message in `run_check` to clearly say "docs are stale" + point at `apidocgen generate` per AC
- [x] Assert the error message content in `test_stale_docs_fail_with_actionable_message` (was only checking return code)
- [x] Add `apidocgen generate` subcommand alias so the AC recipe is a real command
- [x] Add GenerateAliasTests for the new subcommand
- [x] Update action.yml generate step to use `apidocgen generate`
- [x] Update README to use `apidocgen generate` and confirm 3-line badge/snippet present
- [x] Validate `action.yml` / workflows (actionlint passes, YAML valid, if-expressions correct)
- [x] Merge origin/main (issues #6/#7) into branch and resolve main.py conflicts (46 tests pass)

## Final
- [x] Final review pass and merge of origin/main (#6/#7) — 46 tests pass, actionlint clean, drift check green
- [ ] Delete plan file, final commit, push