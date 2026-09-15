# WAR ROOM PLAN — Issue #5: Publish GitHub Action and gate PRs on drift

Branch: `war-room-issue-5` (do not switch). Resumes prior attempt (commits up to `4eb4477`).

## Prior state (already committed)
- [x] `action.yml` at repo root (composite action, inputs: source-dir/config/output/fail-on-drift)
- [x] `.github/workflows/docs.yml` (push→generate+commit, PR→drift check)
- [x] `.github/workflows/test.yml` runs pytest (no longer import-only)
- [x] README badge (docs.yml) + GitHub Action snippet
- [x] Test suite passes locally (19 tests) on the bonus cleanup (ai_enrich removed)

## Gaps found on audit (remaining work)
- [x] Fix `requirements.txt`: `api-doc-generator` is NOT on PyPI → `pip install -r requirements.txt`
      fails in CI (breaks both test.yml and the action install step). Keep only `pyyaml` + `openapi-spec-validator`.
- [x] Add `apidocgen check <project> [--output]` CLI subcommand (per issue: "run `check --fail-on-drift`").
      Regenerates spec in-memory, compares to committed output, exits 1 with a readable
      "docs are stale — run apidocgen generate" message; accepts `--fail-on-drift` flag for parity.
- [x] Refactor `main.py` so scan+generate payload logic is shared by `run_scan` and `run_check`.
- [x] Update `action.yml` drift step to use `apidocgen check --fail-on-drift` (true check-only path,
      don't overwrite the committed output before comparing).
- [x] Add `test` job to `.github/workflows/docs.yml` as required job (`needs`) for generate/check.
- [x] Add unit tests for the `check` subcommand (fresh = exit 0, stale = exit 1).
- [x] README: tighten to a 3-line install snippet + confirm badge (already present).
- [x] Run full pytest suite; all green (24 tests).
- [ ] Remove plan file, final commit referencing #5, push branch.