"""Main CLI tool for API Documentation Generator.

Usage:
    apidocgen <project_path> [--config api-doc.yaml] [--framework ID] ...
    apidocgen generate <project_path> [--fail-on-drift] [--config api-doc.yaml] ...
    apidocgen check <project_path>          # exit 1 on drift (unless check.mode: warn)
    apidocgen diff <project_path>           # print additive->deleted change list
    apidocgen frameworks --list
"""

import argparse
import json
import os
import sys

import config as configlib
import drift as driftlib
import scanner.registry as registry
from generator.openapi import OpenAPIGenerator

COMMANDS = ("generate", "check", "diff", "frameworks")


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
        return _safe_scan(scanner)

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
    for fid in ids:
        scanner = registry.load_scanner(
            fid, project_path, ignore_dirs=ignore_dirs, include=include
        )
        endpoints.extend(_safe_scan(scanner))
    return endpoints


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


# ---------------------------------------------------------------------------
# Shared run plumbing (generate / check / diff)
# ---------------------------------------------------------------------------


def _build_parser(prog, description):
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument(
        "project_path", nargs="?", default=None,
        help="Path to project directory (default: current directory)",
    )
    parser.add_argument(
        "-c", "--config", default=None,
        help="Path to config file (api-doc.yaml / api-doc.json)",
    )
    parser.add_argument(
        "-f", "--framework", default=None,
        help="Framework id to force (see `apidocgen frameworks --list`)",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Spec file path (default: config `output` or api-docs.json)",
    )
    parser.add_argument("-t", "--title", default=None, help="API title")
    parser.add_argument("-v", "--version", default=None, help="API version")
    return parser


def _resolve_run(args, default_path="."):
    """Resolve project path + config + framework + spec file.  Returns None on error."""
    project_path = args.project_path or default_path
    if not os.path.exists(project_path):
        print(f"Error: Project path '{project_path}' does not exist")
        return None

    try:
        cfg = configlib.load_config(args.config)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        return None

    framework = args.framework
    if framework is None and cfg.get("framework") not in (None, "auto"):
        framework = cfg["framework"]

    if framework is not None and framework not in registry.FRAMEWORKS:
        print(
            f"Error: unknown framework '{framework}'. "
            "Run `apidocgen frameworks --list` to see supported frameworks."
        )
        return None

    if framework in registry.PLACEHOLDER_FRAMEWORKS:
        meta = registry.PLACEHOLDER_FRAMEWORKS[framework]
        print(
            f"Error: framework '{framework}' ({meta['name']}) is only a "
            "placeholder - no scanner is implemented for it. Excluded from "
            "auto-detect so it never produces garbage. Run "
            "`apidocgen frameworks --list` to see what IS supported."
        )
        return None

    output = args.output or cfg.get("output") or "api-docs.json"
    return {
        "project_path": project_path,
        "cfg": cfg,
        "framework": framework,
        "output": output,
        "title": args.title or "My API",
        "version": args.version or "1.0.0",
    }


def _generate_spec(project_path, framework, cfg, title, version):
    """Scan the project and build an OpenAPIGenerator for it."""
    endpoints = scan_project(project_path, framework=framework, config=cfg)

    generator = OpenAPIGenerator(title=title, version=version)
    server = cfg.get("server") or {}
    if server.get("url"):
        generator.add_server(server["url"], server.get("description"))

    for endpoint in endpoints:
        generator.add_endpoint(endpoint)
    return generator, endpoints


def _write_spec(generator, output):
    """Serialize the generator to ``output`` (json or yaml)."""
    if output.endswith((".yaml", ".yml")):
        payload = generator.to_yaml()
    else:
        payload = generator.to_json()
    with open(output, "w") as f:
        f.write(payload)
    return payload


def _load_spec_file(output):
    """Decode a spec file on disk; returns the dict, or None if unreadable."""
    try:
        with open(output, "r", errors="ignore") as f:
            text = f.read()
    except OSError as e:
        print(f"Error: cannot read spec '{output}': {e}")
        return None
    try:
        if output.endswith((".yaml", ".yml")):
            import yaml
            return yaml.safe_load(text) or {}
        return json.loads(text) or {}
    except ValueError as e:
        print(f"Error: cannot parse spec '{output}': {e}")
        return None


def _compute_drift(cfg, committed, fresh):
    """Compare committed vs freshly regenerated spec, honoring drift.ignore."""
    ignores = (cfg.get("drift") or {}).get("ignore") or []
    committed_clean = driftlib.remove_ignored(committed or {}, ignores)
    fresh_clean = driftlib.remove_ignored(fresh, ignores)
    return driftlib.detect_drift(committed_clean, fresh_clean)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def run_scan(argv):
    """Legacy positional scan + `apidocgen generate` - scan and write a spec."""
    parser = _build_parser(
        "apidocgen", "API Documentation Generator - Auto-scan projects and generate API specs"
    )
    parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit 1 without writing when the committed spec is stale",
    )
    args = parser.parse_args(argv)

    resolved = _resolve_run(args)
    if resolved is None:
        return 1
    project_path = resolved["project_path"]
    cfg = resolved["cfg"]
    output = resolved["output"]

    print(f"Scanning {project_path} for API endpoints...")
    generator, endpoints = _generate_spec(
        project_path, resolved["framework"], cfg, resolved["title"], resolved["version"]
    )
    print(f"Found {len(endpoints)} endpoints")

    if args.fail_on_drift and os.path.exists(output):
        committed = _load_spec_file(output)
        if committed is None:
            return 1
        changes = _compute_drift(cfg, committed, generator.generate())
        if changes:
            print(
                f"Error: '{output}' is stale - it differs from the current "
                "codebase. Run without --fail-on-drift to update it."
            )
            print(driftlib.render_drift(changes))
            return 1

    _write_spec(generator, output)
    print(f"API documentation generated: {output}")
    return 0


def _check_parser(prog, description):
    parser = _build_parser(prog, description)
    parser.add_argument(
        "--fail-on-drift", action="store_true",
        help="Exit 1 on drift even when check.mode is 'warn'",
    )
    return parser


def run_check(argv):
    """`apidocgen check` - regenerate in-memory, exit 1 on drift unless warn mode."""
    args = _check_parser(
        "apidocgen check",
        "Regenerate the spec in memory and verify the committed spec still "
        "matches the codebase. Exits 1 on drift unless check.mode is 'warn'.",
    ).parse_args(argv)

    resolved = _resolve_run(args)
    if resolved is None:
        return 1
    project_path = resolved["project_path"]
    cfg = resolved["cfg"]
    output = resolved["output"]

    print(f"Scanning {project_path} for API endpoints...")
    generator, endpoints = _generate_spec(
        project_path, resolved["framework"], cfg, resolved["title"], resolved["version"]
    )

    if not os.path.exists(output):
        report = (
            f"Error: committed spec '{output}' not found - nothing documented yet. "
            f"Run `apidocgen generate {project_path}` first."
        )
        print(report)
        return 0 if (not args.fail_on_drift and cfg["check"]["mode"] == "warn") else 1

    committed = _load_spec_file(output)
    if committed is None:
        return 1

    changes = _compute_drift(cfg, committed, generator.generate())
    print(driftlib.render_drift(changes))

    if not changes:
        print(f"{output}: OK - matches the current codebase")
        return 0
    if not args.fail_on_drift and cfg["check"]["mode"] == "warn":
        print(f"{output}: drift detected but check.mode is 'warn' - exiting 0")
        return 0
    return 1


def run_diff(argv):
    """`apidocgen diff` - print the additive->deleted change list (path then item level)."""
    args = _check_parser(
        "apidocgen diff",
        "Print a deterministic additive-to-deleted change list between the "
        "committed spec and the regenerated one. Exits 1 on drift unless "
        "check.mode is 'warn'.",
    ).parse_args(argv)

    resolved = _resolve_run(args)
    if resolved is None:
        return 1
    project_path = resolved["project_path"]
    cfg = resolved["cfg"]
    output = resolved["output"]

    print(f"Scanning {project_path} for API endpoints...")
    generator, endpoints = _generate_spec(
        project_path, resolved["framework"], cfg, resolved["title"], resolved["version"]
    )

    if not os.path.exists(output):
        print(
            f"Error: committed spec '{output}' not found - nothing documented yet. "
            f"Run `apidocgen generate {project_path}` first."
        )
        return 0 if (not args.fail_on_drift and cfg["check"]["mode"] == "warn") else 1

    committed = _load_spec_file(output)
    if committed is None:
        return 1

    changes = _compute_drift(cfg, committed, generator.generate())
    print(driftlib.render_drift(changes, detail=True))

    if not changes:
        print(f"{output}: OK - matches the current codebase")
        return 0
    if not args.fail_on_drift and cfg["check"]["mode"] == "warn":
        print(f"{output}: drift detected but check.mode is 'warn' - exiting 0")
        return 0
    return 1


def main(argv=None):
    """CLI entry point."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in COMMANDS:
        cmd, rest = args[0], args[1:]
        if cmd == "frameworks":
            return run_frameworks(rest)
        if cmd == "generate":
            return run_scan(rest)
        if cmd == "check":
            return run_check(rest)
        if cmd == "diff":
            return run_diff(rest)
    # Legacy positional invocation: `apidocgen <project_path> [...]`.
    return run_scan(args)


if __name__ == "__main__":
    sys.exit(main())