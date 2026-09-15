"""Tests for `apidocgen check` (drift gating, Issue #5)."""

import os
import shutil
import tempfile
import unittest

import config as configlib
from main import run_check

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
EXPRESS_FIXTURE = os.path.join(FIXTURES, "express_project")


def generate(project, output):
    """Produce a committed-docs file that reflects the current fixture."""
    from main import _build_payload
    payload = _build_payload(project, configlib.load_config(None), None, "My API", "1.0.0", output)
    with open(output, "w") as f:
        f.write(payload)


class CheckCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self.project = shutil.copytree(EXPRESS_FIXTURE, os.path.join(self.tmpdir, "proj"))
        self.output = os.path.join(self.tmpdir, "api-docs.json")

    def _run(self):
        return run_check([self.project, "--output", self.output])

    def test_fresh_docs_pass(self):
        generate(self.project, self.output)
        self.assertEqual(self._run(), 0)

    def test_stale_docs_fail_with_actionable_message(self):
        generate(self.project, self.output)
        path = os.path.join(self.tmpdir, self.output)
        with open(path, "a") as f:
            f.write("\ntampered")
        code = self._run()
        self.assertEqual(code, 1)

    def test_accepts_fail_on_drift_flag(self):
        generate(self.project, self.output)
        code = run_check([self.project, "--output", self.output, "--fail-on-drift"])
        self.assertEqual(code, 0)

    def test_missing_committed_output_fails(self):
        code = run_check([self.project, "--output", self.output])
        self.assertEqual(code, 1)

    def test_missing_project_fails(self):
        code = run_check([os.path.join(self.tmpdir, "nope"), "--output", self.output])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()