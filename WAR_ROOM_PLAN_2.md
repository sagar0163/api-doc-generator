# WAR ROOM PLAN — Issue #2: api-doc.yaml config + wire all functional scanners

Branch: `war-room-issue-2`. Commit after each completed subtask.

## Subtasks

- [x] 1. Add `_walk()` + default ignore dirs to `scanner/base.py`
- [x] 2. Create `scanner/registry.py`: framework metadata (supported vs placeholder), per-framework detectors, scanner loading
- [ ] 3. Migrate walk-based scanners to `scanner/_walk()` so config ignore/venv/node_modules filtering is honored everywhere
- [ ] 4. Fix `scanner/gin.py` (dead `sub_pattern` block, group-route handling)
- [ ] 5. Fix `scanner/django.py` (fragile `@api_view` regex, resolves decorated-view routes via `path(...)`)
- [ ] 6. Add `config.py` (defaults, YAML/JSON loading, ignore merging) + `api-doc.yaml` at repo root
- [ ] 7. Rewrite `main.py`: `--config`, expanded `--framework`, `apidocgen frameworks --list`, auto-detect over all supported scanners, placeholder warnings, server.url from config
- [ ] 8. Add `apidocgen` executable launcher script
- [ ] 9. Add `docs/SUPPORTED_FRAMEWORKS.md` matrix reflecting reality
- [ ] 10. Add `tests/` (unittest): django fixture auto-detect, nestjs override, placeholder exclusion + warning, ignore dirs, config loading
- [ ] 11. Update `.github/workflows/test.yml` (+README) to run the new tests
- [ ] 12. Run full test suite; fix failures

## Acceptance mapping

- [ ] Fixture Django project auto-detected -> endpoints (tests: fixture + auto-detect)
- [ ] `--framework nestjs` forces NestJS scanner (tests: override)
- [ ] `frameworks --list` distinguishes supported vs placeholder (registry/list)
- [ ] Auto-detect ignores `node_modules`/`venv`, no error on unrelated files (base `_walk` + defensive detection)
- [ ] Placeholders excluded from auto-detect + warning (registry + main)
- [ ] `SUPPORTED_FRAMEWORKS.md` matches functional scanner list