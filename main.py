"""Main CLI tool for API Documentation Generator.

Usage:
    apidocgen <project_path> [--config api-doc.yaml] [--framework ID] ...
    apidocgen frameworks --list
    apidocgen check <project_path> [--output api-docs.json] [--fail-on-drift]
"""

import argparse
import os
import sys

import config as configlib
import scanner.registry as registry
from generator.openapi import OpenAPIGenerator


def detect_framework(project_path):
    """Auto-detect the primary framework used in the project (legacy API)."""
    detected = registry.detect(project_path)
    return detected[0] if detected else None


def scan_project(project_path, framework=None, config=None, warn=None):
    """Scan ``project_path`` for API endpoints.

    ``framework`` may be a framework id or None for auto-detection.
    ``config`` is a merged config dict (see config.py).  ``warn`` is a
    callable used to surface warnings; defaults to ``print``.
    """
    cfg = config or configlib.DEFAULT_CONFIG
    warn = warn or (lambda msg: print(f"Warning: {msg}"))
    ignore_dirs = cfg.get("ignore", [])
    include = cfg.get("include") or None

    # Auto-detection never considers placeholder scanners; explain that once.
    placeholders = registry.placeholder_frameworks()
    if placeholders:
        warn(
            "skipping placeholder scanner(s): {} - no implementation, "
            "excluded from auto-detect".format(", ".join(sorted(placeholders)))
        )

    if framework is not None:
        # Explicit override: must be supported, otherwise fail loudly.
        cls = registry.get_scanner_class(framework)
        scanner = cls(project_path, ignore_dirs=ignore_dirs, include=include)
        eps = _safe_scan(scanner)
        schemas = scanner.schemas if hasattr(scanner, 'schemas') else {}
        return eps, schemas

    detected = registry.detect(project_path)
    if detected:
        ids = detected
    else:
        warn(
            "no framework detected in '{}'; scanning with all supported "
            "scanners".format(project_path)
        )
        # gin_enhanced duplicates gin's output; dropped from the fallback set.
        ids = [fid for fid in registry.SUPPORTED_FRAMEWORKS if fid != "gin_enhanced"]

    endpoints = []
    schemas = {}
    for fid in ids:
        scanner = registry.load_scanner(
            fid, project_path, ignore_dirs=ignore_dirs, include=include
        )
        eps = _safe_scan(scanner)
        endpoints.extend(eps)
        if hasattr(scanner, 'schemas') and scanner.schemas:
            schemas.update(scanner.schemas)
    return endpoints, schemas


def _safe_scan(scanner):
    """Scan and surface scanner errors without aborting the whole run."""
    try:
        return scanner.scan() or []
    except Exception as e:  # noqa: BLE001 - a broken scanner must not kill the run
        print(f"Warning: scanner for {scanner.__class__.__name__} failed: {e}")
        return []


def run_frameworks(argv):
    """`apidocgen frameworks [--list]` - show supported vs placeholder scanners."""
    parser = argparse.ArgumentParser(
        prog="apidocgen frameworks",
        description="List supported and placeholder framework scanners.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List framework scanners (default behavior).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print a rendered matrix of supported frameworks.",
    )
    args = parser.parse_args(argv)

    supported = registry.supported_frameworks()
    placeholders = registry.placeholder_frameworks()

    if args.list or not args.pretty:
        cols_s = (max(len(i) for i in supported) + 2, max(len(m["language"]) for m in supported.values()) + 2)
        cols_p = (max(len(i) for i in placeholders) + 2, max(len(m["language"]) for m in placeholders.values()) + 2)

        print("Supported frameworks (work today, used by auto-detect):")
        print(f"  {'ID':<{cols_s[0]}}{'Language':<{cols_s[1]}}Notes")
        for fid, meta in sorted(supported.items()):
            print(
                f"  {fid:<{cols_s[0]}}{meta['language']:<{cols_s[1]}}{meta['notes']}"
            )
        print()
        print("Placeholder frameworks (stub files, no implementation - excluded from auto-detect):")
        print(f"  {'ID':<{cols_p[0]}}{'Language':<{cols_p[1]}}Notes")
        for fid, meta in sorted(placeholders.items()):
            print(
                f"  {fid:<{cols_p[0]}}{meta['language']:<{cols_p[1]}}{meta['notes']}"
            )
        return

    print_matrix(supported, placeholders)


def print_matrix(supported, placeholders):
    """Compact matrix of supported frameworks."""
    print("Framework scanners:")
    print(f"{'id':<14}{'language':<10}{'status':<12}scanner")
    for fid, meta in sorted(supported.items()):
        print(
            f"{fid:<14}{meta['language']:<10}{'supported':<12}"
            f"{meta['module']}.{meta['cls']}"
        )
    for fid, meta in sorted(placeholders.items()):
        print(f"{fid:<14}{meta['language']:<10}{'placeholder':<12}-")


def run_scan(argv):
    """`apidocgen <project_path> [...]` - scan a project and emit a spec."""
    parser = argparse.ArgumentParser(
        prog="apidocgen",
        description="API Documentation Generator - Auto-scan projects and generate API specs",
    )
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument(
        "-c", "--config", default=None,
        help="Path to config file (api-doc.yaml / api-doc.json)",
    )
    parser.add_argument(
        "-f", "--framework", default=None,
        help="Framework id to force (see `apidocgen frameworks --list`)",
    )
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    parser.add_argument("-t", "--title", default=None, help="API title")
    parser.add_argument("-v", "--version", default=None, help="API version")

    args = parser.parse_args(argv)

    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        return 1

    try:
        cfg = configlib.load_config(args.config)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        return 1

    framework = _resolve_framework(args.framework, cfg)
    if framework is not None:
        err = _validate_framework(framework)
        if err is not None:
            print(err)
            return 1

    output = args.output or cfg.get("output") or "api-docs.json"
    title = args.title or "My API"
    version = args.version or "1.0.0"

    print(f"Scanning {args.project_path} for API endpoints...")

    payload = _build_payload(args.project_path, cfg, framework, title, version, output)

    with open(output, "w") as f:
        f.write(payload)

    print(f"API documentation generated: {output}")
    return 0


def run_check(argv):
    """`apidocgen check <project_path> [...]` - fail when committed docs are stale.

    Regenerates the spec in memory and compares it against the committed
    ``--output`` file.  Exits non-zero with an actionable message when the two
    differ, so CI can gate PRs on documentation drift.  ``--fail-on-drift`` is
    accepted for parity with the GitHub Action input; checking always fails on
    drift.
    """
    parser = argparse.ArgumentParser(
        prog="apidocgen check",
        description="Check that committed API docs match the current source.",
    )
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument(
        "-c", "--config", default=None,
        help="Path to config file (api-doc.yaml / api-doc.json)",
    )
    parser.add_argument(
        "-f", "--framework", default=None,
        help="Framework id to force (see `apidocgen frameworks --list`)",
    )
    parser.add_argument("-o", "--output", default=None, help="Committed spec file to compare")
    parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Fail when committed docs differ from generated docs (always-on).",
    )

    args = parser.parse_args(argv)

    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        return 1

    try:
        cfg = configlib.load_config(args.config)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        return 1

    framework = _resolve_framework(args.framework, cfg)
    if framework is not None:
        err = _validate_framework(framework)
        if err is not None:
            print(err)
            return 1

    output = args.output or cfg.get("output") or "api-docs.json"

    if not os.path.exists(output):
        print(
            f"Error: committed docs file '{output}' not found. "
            "Run `apidocgen <project_path> --output {0}` to generate it.".format(output)
        )
        return 1

    print(f"Scanning {args.project_path} for API endpoints...")

    payload = _build_payload(args.project_path, cfg, framework, "My API", "1.0.0", output)

    with open(output) as f:
        committed = f.read()

    if payload == committed:
        print(f"Docs are up to date: {output}")
        return 0

    print(
        f"::error::docs are stale - {output} does not match the generated output."
    )
    print(
        f"::error::run `apidocgen {args.project_path} --output {output}` (or push through "
        "ci: `uses: sagar0163/api-doc-generator@main` with `fail-on-drift: true`), "
        "commit the regenerated spec, and re-push."
    )
    return 1


def _resolve_framework(cli_framework, cfg):
    """Pick the framework: CLI flag wins, then config, then None for auto."""
    framework = cli_framework
    if framework is None and cfg.get("framework") not in (None, "auto"):
        framework = cfg["framework"]
    return framework


def _validate_framework(framework):
    """Return an error message string, or None if ``framework`` is usable."""
    if framework not in registry.FRAMEWORKS:
        return (
            f"Error: unknown framework '{framework}'. "
            "Run `apidocgen frameworks --list` to see supported frameworks."
        )
    if framework in registry.PLACEHOLDER_FRAMEWORKS:
        meta = registry.PLACEHOLDER_FRAMEWORKS[framework]
        return (
            f"Error: framework '{framework}' ({meta['name']}) is only a "
            "placeholder - no scanner is implemented for it. Excluded from "
            "auto-detect so it never produces garbage. Run "
            "`apidocgen frameworks --list` to see what IS supported."
        )
    return None


def _build_payload(project_path, cfg, framework, title, version, output):
    """Scan ``project_path`` and render the spec payload (yaml or json)."""
    endpoints, schemas = scan_project(project_path, framework=framework, config=cfg)

    print(f"Found {len(endpoints)} endpoints")

    generator = OpenAPIGenerator(title=title, version=version)
    server = cfg.get("server") or {}
    if server.get("url"):
        generator.add_server(server["url"], server.get("description"))

    for endpoint in endpoints:
        generator.add_endpoint(endpoint)

    for name, schema in schemas.items():
        generator.add_schema(name, schema)

    if output.endswith((".yaml", ".yml")):
        return generator.to_yaml()
    return generator.to_json()


def main(argv=None):
    """CLI entry point."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "frameworks":
        return run_frameworks(args[1:])
    if args and args[0] == "check":
        return run_check(args[1:])
    return run_scan(args)


if __name__ == "__main__":
    sys.exit(main())