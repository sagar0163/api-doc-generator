"""End-to-end / acceptance tests for Issue #2.

Covers: auto-detect of a Django fixture, forced `--framework` override,
placeholder exclusion from auto-detect (with warning), ignore of
node_modules/venv, and config loading.
"""

import json
import os
import tempfile
import unittest

import config as configlib
import scanner.registry as registry
from main import scan_project

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
DJANGO_FIXTURE = os.path.join(FIXTURES, "django_project")
EXPRESS_FIXTURE = os.path.join(FIXTURES, "express_project")
NESTJS_FIXTURE = os.path.join(FIXTURES, "nestjs_project")


class Warnings:
    def __init__(self):
        self.messages = []

    def __call__(self, msg):
        self.messages.append(msg)

    def text(self):
        return "\n".join(self.messages)


class AutoDetectTests(unittest.TestCase):
    def test_django_fixture_auto_detected(self):
        """Issue #2 acceptance: a Django project is detected with no flags."""
        warnings = Warnings()
        endpoints, _ = scan_project(DJANGO_FIXTURE, framework=None, warn=warnings)
        paths = {(ep.method, ep.path) for ep in endpoints}
        self.assertIn(("GET", "users/"), paths)
        self.assertIn(("POST", "users/"), paths)
        self.assertIn(("GET", "health/"), paths)
        # garbage in node_modules / venv must never leak in
        for ep in endpoints:
            self.assertNotIn("node_modules", ep.handler)
            self.assertNotIn("venv", ep.handler)

    def test_detection_ignores_node_modules_and_venv(self):
        """A fake express package.json lives under node_modules - ignored."""
        detected = registry.detect(DJANGO_FIXTURE)
        self.assertNotIn("express", detected)
        self.assertIn("django", detected)

    def test_placeholder_warning_emitted(self):
        warnings = Warnings()
        scan_project(DJANGO_FIXTURE, framework=None, warn=warnings)
        self.assertIn("placeholder", warnings.text())
        self.assertIn("axum", warnings.text())


class OverrideTests(unittest.TestCase):
    def test_framework_override_forces_nestjs(self):
        """Issue #2 acceptance: --framework nestjs forces the NestJS scanner."""
        warnings = Warnings()
        # This tree is a Django project (no package.json at all), but the
        # fake .ts file proves the NestJS scanner ran.
        endpoints, _ = scan_project(DJANGO_FIXTURE, framework="nestjs", warn=warnings)
        self.assertTrue(endpoints)
        self.assertTrue(all(ep.handler.endswith(".ts") for ep in endpoints))
        paths = {(ep.method, ep.path) for ep in endpoints}
        self.assertIn(("GET", "/legacy/items"), paths)

    def test_framework_override_not_from_detection(self):
        detected = registry.detect(NESTJS_FIXTURE)
        self.assertIn("nestjs", detected)
        endpoints, _ = scan_project(NESTJS_FIXTURE, framework="nestjs", warn=Warnings())
        paths = {(ep.method, ep.path) for ep in endpoints}
        self.assertIn(("GET", "/api/users"), paths)

    def test_placeholder_override_raises(self):
        with self.assertRaises(ValueError):
            scan_project(DJANGO_FIXTURE, framework="axum", warn=Warnings())

    def test_unknown_override_raises(self):
        with self.assertRaises(KeyError):
            scan_project(DJANGO_FIXTURE, framework="not-a-framework", warn=Warnings())


class IgnoreConfigTests(unittest.TestCase):
    def test_explicit_ignore_dir_respected(self):
        warnings = Warnings()
        cfg = configlib.DEFAULT_CONFIG.copy()
        cfg["ignore"] = list(cfg["ignore"]) + ["legacy"]
        endpoints, _ = scan_project(DJANGO_FIXTURE, framework="nestjs", config=cfg, warn=warnings)
        # 'legacy' is ignored, so the forced NestJS scan finds nothing.
        self.assertEqual(endpoints, [])

    def test_include_patterns_respected(self):
        warnings = Warnings()
        cfg = configlib.DEFAULT_CONFIG.copy()
        cfg["include"] = ["**/*.py"]
        endpoints, _ = scan_project(DJANGO_FIXTURE, framework=None, config=cfg, warn=warnings)
        self.assertTrue(all(ep.handler.endswith(".py") for ep in endpoints))


class ConfigLoadingTests(unittest.TestCase):
    def test_default_api_doc_yaml_exists(self):
        self.assertTrue(os.path.exists("api-doc.yaml"))
        cfg = configlib.load_config("api-doc.yaml")
        self.assertEqual(cfg["framework"], "auto")
        self.assertIn("node_modules", cfg["ignore"])
        self.assertEqual(cfg["server"]["url"], "http://localhost:3000")

    def test_ignore_is_additive_with_defaults(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
            f.write('{"ignore": ["custom_dir"]}')
            f.flush()
            cfg = configlib.load_config(f.name)
        self.assertIn("node_modules", cfg["ignore"])
        self.assertIn("custom_dir", cfg["ignore"])

    def test_framework_from_config(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
            f.write('{"framework": "express"}')
            f.flush()
            cfg = configlib.load_config(f.name)
        self.assertEqual(cfg["framework"], "express")

    def test_missing_config_raises(self):
        with self.assertRaises(ValueError):
            configlib.load_config("does-not-exist.yaml")


class RegistryTests(unittest.TestCase):
    def test_placeholders_distinct_from_supported(self):
        supported = registry.supported_frameworks()
        placeholders = registry.placeholder_frameworks()
        for pid in placeholders:
            self.assertNotIn(pid, supported)
        for pid in ("axum", "apirouter", "grails", "vertx", "blueprint"):
            self.assertIn(pid, placeholders)
        self.assertIn("django", supported)
        self.assertIn("nestjs", supported)

    def test_placeholders_have_no_scanner_class(self):
        for meta in registry.placeholder_frameworks().values():
            self.assertIsNone(meta["cls"])

    def test_gin_scanner_group_prefixes_and_drops_garbage(self):
        from scanner.gin import GinScanner
        scanner = GinScanner(os.path.join(FIXTURES, "gin_project"))
        paths = {(ep.method, ep.path) for ep in scanner.scan()}
        self.assertIn(("GET", "/health"), paths)
        self.assertIn(("GET", "/api/v1/users"), paths)


if __name__ == "__main__":
    unittest.main()

class ExportCommandTests(unittest.TestCase):
    """Issue #6: `apidocgen export --html out.html [--spec spec.json]`."""

    def test_export_writes_self_contained_html(self):
        from main import main
        with tempfile.TemporaryDirectory() as d:
            spec = os.path.join(d, "spec.json")
            out = os.path.join(d, "docs.html")
            with open(spec, "w") as f:
                f.write('{"openapi":"3.0.3","info":{"title":"CLI API","version":"1.0"},'
                        '"paths":{"/x":{"get":{"responses":{"200":{"description":"ok"}}}}}}')
            rc = main(["export", "--html", out, "--spec", spec, "--title", "CLI Title", "--timestamp"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(out))
            with open(out, "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("<title>CLI Title</title>", html)
            self.assertIn("SwaggerUIBundle", html)
            self.assertIn("CLI API", html)  # spec embedded
            self.assertIn("Generated by apidocgen on", html)
            self.assertNotIn("unpkg.com", html)

    def test_export_missing_spec_errors(self):
        from main import main
        with tempfile.TemporaryDirectory() as d:
            rc = main(["export", "--html", os.path.join(d, "x.html"), "--spec", "nope.json"])
        self.assertEqual(rc, 1)

    def test_export_requires_html_flag(self):
        from main import main
        with self.assertRaises(SystemExit):
            main(["export", "--spec", "api-docs.json"])


class ServeCommandTests(unittest.TestCase):
    """Issue #6: `apidocgen serve [--spec spec.json]` serves the standalone page."""

    def test_serve_missing_spec_errors(self):
        from main import main
        self.assertEqual(main(["serve", "--spec", "does-not-exist.json"]), 1)

    def test_serve_dispatches_to_serve_module(self):
        from unittest import mock
        from main import main
        spec = {"openapi": "3.0.3", "info": {"title": "S", "version": "1"}, "paths": {}}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "api-docs.json")
            with open(path, "w") as f:
                json.dump(spec, f)
            with mock.patch("serve.serve") as fake:
                rc = main(["serve", "--spec", path, "--port", "9999", "--host", "127.0.0.1"])
        self.assertEqual(rc, 0)
        fake.assert_called_once_with(path, 9999, host="127.0.0.1", title=None)
