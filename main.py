"""Main CLI tool for API Documentation Generator.

Usage:
    apidocgen <project_path> [--config api-doc.yaml] [--framework ID] ...
    apidocgen frameworks --list
    apidocgen export --html out.html [--spec spec.json] [--title "X"]
    apidocgen serve [--spec spec.json] [--port PORT]
"""

import argparse
import datetime
import json
import os
import sys

import config as configlib
import scanner.registry as registry
import ai_enrich
from generator.html import build_standalone_html
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
    parser.add_argument("--ai-enrich", action="store_true", help="Enable AI enrichment for descriptions and examples")

    args = parser.parse_args(argv)

    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        return 1

    try:
        cfg = configlib.load_config(args.config)
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        return 1

    framework = args.framework
    if framework is None and cfg.get("framework") not in (None, "auto"):
        framework = cfg["framework"]

    if framework is not None and framework not in registry.FRAMEWORKS:
        print(
            f"Error: unknown framework '{framework}'. "
            "Run `apidocgen frameworks --list` to see supported frameworks."
        )
        return 1

    if framework in registry.PLACEHOLDER_FRAMEWORKS:
        meta = registry.PLACEHOLDER_FRAMEWORKS[framework]
        print(
            f"Error: framework '{framework}' ({meta['name']}) is only a "
            "placeholder - no scanner is implemented for it. Excluded from "
            "auto-detect so it never produces garbage. Run "
            "`apidocgen frameworks --list` to see what IS supported."
        )
        return 1

    output = args.output or cfg.get("output") or "api-docs.json"
    title = args.title or "My API"
    version = args.version or "1.0.0"

    print(f"Scanning {args.project_path} for API endpoints...")

    endpoints, schemas = scan_project(args.project_path, framework=framework, config=cfg)

    print(f"Found {len(endpoints)} endpoints")

    generator = OpenAPIGenerator(title=title, version=version)
    server = cfg.get("server") or {}
    if server.get("url"):
        generator.add_server(server["url"], server.get("description"))

    for endpoint in endpoints:
        generator.add_endpoint(endpoint)
        
    for name, schema in schemas.items():
        generator.add_schema(name, schema)

    spec = generator.generate()

    if args.ai_enrich or cfg.get("ai", {}).get("enabled"):
        ai_cfg = cfg.get("ai", {})
        try:
            spec = ai_enrich.enrich_spec(spec, ai_cfg)
        except Exception as e:
            print(f"Error during AI enrichment: {e}")
            return 1

    import yaml
    import json
    if output.endswith((".yaml", ".yml")):
        payload = yaml.dump(spec, sort_keys=False)
    else:
        payload = json.dumps(spec, indent=2)

    with open(output, "w") as f:
        f.write(payload)

    print(f"API documentation generated: {output}")
    return 0


def _load_spec_text(spec_path):
    """Read a spec file and return (spec_json_str, spec_dict)."""
    with open(spec_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if spec_path.lower().endswith((".yaml", ".yml")):
        import yaml
        spec_dict = yaml.safe_load(raw)
        return json.dumps(spec_dict, indent=2), spec_dict
    spec_dict = json.loads(raw) if raw.strip().startswith(("{", "[")) else None
    return raw, spec_dict


def run_export(argv):
    """`apidocgen export --html out.html [...]` - emit a self-contained HTML page."""
    parser = argparse.ArgumentParser(
        prog="apidocgen export",
        description=(
            "Export the API spec as a single self-contained HTML file "
            "with all Swagger UI assets inlined (works offline)."
        ),
    )
    parser.add_argument("--html", required=True, help="Output HTML file path")
    parser.add_argument(
        "--spec", default="api-docs.json", help="Path to the OpenAPI spec (default api-docs.json)"
    )
    parser.add_argument("--title", default=None, help="Page title override")
    parser.add_argument("--icon", default=None, help="Favicon image to embed")
    parser.add_argument(
        "--timestamp", action="store_true", help="Embed a 'generated at' timestamp"
    )
    args = parser.parse_args(argv)

    if not os.path.exists(args.spec):
        print(f"Error: spec file '{args.spec}' does not exist")
        return 1

    try:
        _, spec_dict = _load_spec_text(args.spec)
    except (ValueError, RuntimeError) as e:
        print(f"Error: could not read spec '{args.spec}': {e}")
        return 1

    generated_at = None
    if args.timestamp:
        generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = build_standalone_html(
        spec_dict, title=args.title, icon=args.icon, generated_at=generated_at
    )

    with open(args.html, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(args.html) / 1024
    print(f"Exported self-contained HTML: {args.html} ({size_kb:.0f} KB)")
    print("All Swagger UI assets are inlined - open this file with networking disabled.")
    return 0


def run_serve(argv):
    """`apidocgen serve [--spec spec.json] [--port P]` - serve the standalone page."""
    parser = argparse.ArgumentParser(
        prog="apidocgen serve",
        description="Serve the self-contained Swagger UI page (no CDN references).",
    )
    parser.add_argument("--spec", default="api-docs.json", help="Path to the OpenAPI spec")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--title", default=None, help="Page title override")
    args = parser.parse_args(argv)

    if not os.path.exists(args.spec):
        print(f"Error: spec file '{args.spec}' does not exist")
        return 1

    import serve as serve_mod
    try:
        serve_mod.serve(args.spec, args.port, host=args.host, title=args.title)
    except KeyboardInterrupt:
        pass
    return 0


def main(argv=None):
    """CLI entry point."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "frameworks":
        return run_frameworks(args[1:])
    if args and args[0] == "export":
        return run_export(args[1:])
    if args and args[0] == "serve":
        return run_serve(args[1:])
    return run_scan(args)


if __name__ == "__main__":
    sys.exit(main())