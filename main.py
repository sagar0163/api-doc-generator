"""Backward-compatible wrapper around the `apidocgen` CLI."""

import sys

from apidocgen import cli

detect_framework = cli.detect_framework
scan_project = cli.scan_project


def main(argv=None):
    """Run the apidocgen CLI, defaulting to the `generate` subcommand."""
    args = list(sys.argv[1:] if argv is None else argv)

    # Preserve the legacy `python main.py <path>` invocation by
    # defaulting to the `generate` subcommand.
    if args and args[0] not in ("generate", "serve", "-h", "--help"):
        args = ["generate"] + args

    cli.main(args)


if __name__ == "__main__":
    main()