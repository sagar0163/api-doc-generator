"""Tests for the `apidocgen` CLI (Issue #1)."""

import json
from pathlib import Path

import pytest
import yaml

from apidocgen import cli
from main import main as main_wrapper

FIXTURE = Path(__file__).resolve().parent.parent / "fixture"


def test_help_lists_subcommands(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    assert "generate" in out
    assert "serve" in out


def test_generate_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["generate", "--help"])
    out = capsys.readouterr().out
    assert "--format" in out
    assert "--framework" in out


@pytest.mark.parametrize("fmt", ["json", "yaml"])
def test_generate_output(tmp_path, capsys, fmt):
    out = tmp_path / f"api-docs.{fmt}"
    cli.main(["generate", str(FIXTURE), "-o", str(out), "--format", fmt,
              "--title", "Test API", "--version", "2.0.0", "--framework", "flask"])
    capsys.readouterr()

    assert out.exists()
    raw = out.read_text()

    if fmt == "json":
        spec = json.loads(raw)
    else:
        spec = yaml.safe_load(raw)

    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "Test API"
    assert spec["info"]["version"] == "2.0.0"
    assert "/users" in spec["paths"]


def test_main_wrapper_preserves_legacy_invocation(tmp_path, capsys):
    out = tmp_path / "legacy.yaml"
    main_wrapper([str(FIXTURE), "-o", str(out), "--format", "yaml"])
    capsys.readouterr()

    assert out.exists()
    spec = yaml.safe_load(out.read_text())
    assert spec["openapi"] == "3.0.3"
    assert "/users" in spec["paths"]