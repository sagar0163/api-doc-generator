"""Drift detection tests for Issue #4.

Covers every acceptance criterion:
- two consecutive `generate` runs produce byte-identical output
- adding/changing/removing endpoints or schemas flips `check` to exit 1
  and lists the change
- `diff` shows added/removed/changed operations (path then item level)
- `--fail-on-drift` gates `generate`'s exit code on a stale committed spec
- `check.mode: warn` prints but exits 0
- `drift.ignore` suppresses configured keys without hiding real drift
"""

import contextlib
import copy
import io
import json
import os
import tempfile
import unittest

from config import DEFAULT_CONFIG, load_config
import drift as driftlib
import main
from tests.test_main import DJANGO_FIXTURE


def run_cli(args):
    """Run the CLI, capturing stdout; returns (exit_code, stdout)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = main.main(args)
    return rc, out.getvalue()


class DriftHarness(unittest.TestCase):
    """Shared helpers: a temp config + a committed spec for the Django fixture."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name
        self.spec = os.path.join(self.dir, "api-docs.json")
        self.cfg = os.path.join(self.dir, "api-doc.json")
        self._write_config({})

    def _write_config(self, extra):
        cfg = {"output": self.spec}
        cfg.update(extra)
        with open(self.cfg, "w") as f:
            json.dump(cfg, f)

    def generate(self, *extra):
        return run_cli(["generate", DJANGO_FIXTURE, "-c", self.cfg, *extra])

    def read_spec(self):
        with open(self.spec) as f:
            return json.load(f)

    def write_spec(self, spec):
        with open(self.spec, "w") as f:
            json.dump(spec, f, sort_keys=True)

    def committed_without(self, *paths):
        """Committed spec = fresh spec with those paths deleted."""
        spec = self.read_spec()
        for p in paths:
            del spec["paths"][p]
        self.write_spec(spec)
        return spec


class DeterministicGenerateTests(DriftHarness):
    def test_consecutive_generates_are_byte_identical(self):
        rc1, _ = self.generate()
        first = self.read_spec()
        with open(self.spec, "rb") as f:
            bytes1 = f.read()
        rc2, _ = self.generate()
        with open(self.spec, "rb") as f:
            bytes2 = f.read()
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertEqual(self.read_spec(), first)
        self.assertEqual(bytes1, bytes2, "identical runs must produce identical bytes")


class CheckTests(DriftHarness):
    def test_check_passes_when_spec_is_current(self):
        self.generate()
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 0)
        self.assertIn("No drift detected", out)

    def test_check_fails_on_added_endpoint(self):
        self.generate()
        self.committed_without("users/")
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("+ users/ (added)", out)

    def test_check_fails_on_removed_endpoint(self):
        self.generate()
        spec = self.read_spec()
        spec["paths"]["/gone"] = copy.deepcopy(next(iter(spec["paths"].values())))
        self.write_spec(spec)
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("- /gone (removed)", out)

    def test_check_fails_on_changed_path(self):
        self.generate()
        spec = self.read_spec()
        spec["paths"]["members/"] = spec["paths"].pop("users/")
        self.write_spec(spec)
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("+ users/ (added)", out)
        self.assertIn("- members/ (removed)", out)

    def test_check_fails_on_schema_change(self):
        self.generate()
        spec = self.read_spec()
        spec["paths"]["users/"]["get"]["parameters"] = [
            {"name": "id", "in": "query", "schema": {"type": "string"}}
        ]
        self.write_spec(spec)
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("~ users/ (changed)", out)


class DiffTests(DriftHarness):
    def test_diff_shows_added(self):
        self.generate()
        self.committed_without("users/")
        rc, out = run_cli(["diff", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("+ users/ (added)", out)

    def test_diff_lists_item_level_changes_under_changed_path(self):
        self.generate()
        spec = self.read_spec()
        spec["paths"]["users/"]["get"]["responses"]["200"]["description"] = "Stale"
        self.write_spec(spec)
        rc, out = run_cli(["diff", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("~ users/ (changed)", out)
        self.assertIn("~ get.responses.200.description", out)

    def test_check_report_is_path_level_only(self):
        """The `check` report is concise; item lines only appear in `diff`."""
        self.generate()
        spec = self.read_spec()
        spec["paths"]["users/"]["get"]["responses"]["200"]["description"] = "Stale"
        self.write_spec(spec)
        _, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertIn("~ users/ (changed)", out)
        self.assertNotIn("get.responses.200.description", out)


class GenerateFailOnDriftTests(DriftHarness):
    def test_fail_on_drift_gates_stale_generate(self):
        self.generate()
        self.committed_without("users/")
        with open(self.spec, "rb") as f:
            stale_bytes = f.read()
        rc, out = self.generate("--fail-on-drift")
        self.assertEqual(rc, 1)
        self.assertIn("stale", out)
        # the stale committed spec is preserved; generate must not clobber it
        with open(self.spec, "rb") as f:
            self.assertEqual(f.read(), stale_bytes)

    def test_fail_on_drift_passes_when_current(self):
        self.generate()
        rc, out = self.generate("--fail-on-drift")
        self.assertEqual(rc, 0)
        self.assertIn("API documentation generated", out)


class WarnModeTests(DriftHarness):
    def test_warn_mode_prints_but_exits_zero(self):
        self._write_config({"check": {"mode": "warn"}})
        self.generate()
        self.committed_without("users/")
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 0)
        self.assertIn("Drift detected", out)
        self.assertIn("check.mode is 'warn'", out)

    def test_warn_mode_overridden_by_fail_on_drift(self):
        self._write_config({"check": {"mode": "warn"}})
        self.generate()
        self.committed_without("users/")
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg, "--fail-on-drift"])
        self.assertEqual(rc, 1)

    def test_invalid_check_mode_rejected(self):
        self._write_config({"check": {"mode": "explode"}})
        rc, out = run_cli(["generate", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("invalid check.mode", out)


class DriftIgnoreTests(DriftHarness):
    def test_ignore_suppresses_configured_key(self):
        self._write_config({"drift": {"ignore": ["info.description"]}})
        self.generate()
        spec = self.read_spec()
        spec["info"]["description"] = "Hand-maintained description"
        self.write_spec(spec)
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 0, "info.description must be ignored: " + out)

    def test_ignore_does_not_hide_real_drift(self):
        self._write_config({"drift": {"ignore": ["info.description"]}})
        self.generate()
        spec = self.read_spec()
        spec["info"]["description"] = "Hand-maintained description"
        spec["paths"]["users/"]["get"]["parameters"] = [{"name": "id", "in": "query"}]
        self.write_spec(spec)
        rc, out = run_cli(["check", DJANGO_FIXTURE, "-c", self.cfg])
        self.assertEqual(rc, 1)
        self.assertIn("~ users/ (changed)", out)

    def test_wildcard_ignore_suppresses_nested_examples(self):
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "T", "version": "1", "description": "d"},
            "paths": {"/a": {"get": {"responses": {"200": {"example": {"kept": 1}}}}}},
        }
        changed = copy.deepcopy(spec)
        changed["paths"]["/a"]["get"]["responses"]["200"]["example"] = {"totally": "different"}
        ignored = driftlib.detect_drift(
            driftlib.remove_ignored(spec, ["**.example"]),
            driftlib.remove_ignored(changed, ["**.example"]),
        )
        self.assertEqual(ignored, {})
        # without the ignore, the same change is a drift
        self.assertIn("paths", driftlib.detect_drift(spec, changed))


class DriftUnitTests(unittest.TestCase):
    def test_detect_drift_added_removed_changed_semantics(self):
        committed = {
            "openapi": "3.0.3",
            "info": {"title": "A", "version": "1"},
            "paths": {
                "/left": {"get": {"summary": "s"}},
                "/same": {"get": {"summary": "s"}},
            },
        }
        fresh = {
            "openapi": "3.0.3",
            "info": {"title": "A", "version": "1"},
            "paths": {
                "/same": {"get": {"summary": "s"}},
                "/right": {"get": {"summary": "s"}},
            },
        }
        changes = driftlib.detect_drift(committed, fresh)
        self.assertEqual(changes["paths"]["/left"]["type"], "removed")
        self.assertEqual(changes["paths"]["/right"]["type"], "added")
        self.assertNotIn("/same", changes["paths"])

    def test_detect_drift_new_top_level_key_reported(self):
        changes = driftlib.detect_drift(
            {"info": {"a": 1}}, {"info": {"a": 1}, "components": {"x": 1}}
        )
        self.assertEqual(changes["other"]["diffs"][0][0], "components")
        self.assertIsNone(changes["other"]["diffs"][0][1])

    def test_render_drift_absent(self):
        self.assertEqual(driftlib.render_drift({}), "No drift detected.")

    def test_match_path_wildcards(self):
        self.assertTrue(driftlib._match_path("info.description", "info.**"))
        self.assertTrue(driftlib._match_path("paths./a.get.example", "**.example"))
        self.assertTrue(driftlib._match_path("a.b.example", "**.example"))
        self.assertFalse(driftlib._match_path("a.b.examplex", "**.example"))
        self.assertFalse(driftlib._match_path("a.b.c", "*.c"))
        self.assertTrue(driftlib._match_path("b.c", "*.c"))


class ConfigModeValidationTests(unittest.TestCase):
    def test_default_config_has_check_and_drift(self):
        self.assertEqual(DEFAULT_CONFIG["check"]["mode"], "fail")
        self.assertEqual(DEFAULT_CONFIG["drift"]["ignore"], [])

    def test_check_mode_merged_nested_with_defaults(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"check": {"mode": "warn"}}')
            cfg_path = f.name
        try:
            cfg = load_config(cfg_path)
            self.assertEqual(cfg["check"]["mode"], "warn")
            self.assertEqual(cfg["drift"]["ignore"], [])
        finally:
            os.unlink(cfg_path)

    def test_invalid_check_mode_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"check": {"mode": "bad"}}')
            cfg_path = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(cfg_path)
        finally:
            os.unlink(cfg_path)


if __name__ == "__main__":
    unittest.main()