"""Core scanner module - Base classes for API detection"""

import fnmatch
import os


DEFAULT_IGNORE_DIRS = [
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".gradle",
    ".idea",
    ".vscode",
    "vendor",
    "bower_components",
    "bin",
    "obj",
    "migrations",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "coverage",
]


class APIScanner:
    """Base class for API endpoint scanners."""

    def __init__(self, project_path, ignore_dirs=None, include=None):
        self.project_path = project_path
        self.endpoints = []
        self.ignore_dirs = (
            list(DEFAULT_IGNORE_DIRS)
            if ignore_dirs is None
            else list(DEFAULT_IGNORE_DIRS) + list(ignore_dirs)
        )
        self.include_patterns = list(include) if include else []

    def scan(self):
        """Scan project for API endpoints."""
        raise NotImplementedError

    def get_endpoints(self):
        """Return discovered endpoints."""
        return self.endpoints

    def is_ignored(self, name):
        """Return True if a directory/file name matches an ignore pattern."""
        for pattern in self.ignore_dirs:
            if name == pattern or fnmatch.fnmatch(name, pattern):
                return True
        return False

    def _walk(self, exts=None):
        """Yield file paths under the project, skipping ignored dirs.

        Only files whose name ends with one of ``exts`` (if given) are
        yielded.  ``exts`` may be a str or an iterable of str.  If
        ``include`` patterns were set on the scanner, only files matching at
        least one pattern (relative path or base name) are yielded.
        """
        if isinstance(exts, str):
            exts = (exts,)
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self.is_ignored(d)]
            for file in sorted(files):
                if exts and not file.endswith(tuple(exts)):
                    continue
                full = os.path.join(root, file)
                if self.include_patterns:
                    rel = os.path.relpath(full, self.project_path).replace(os.sep, "/")
                    if not (
                        any(fnmatch.fnmatch(rel, p) for p in self.include_patterns)
                        or any(fnmatch.fnmatch(file, p) for p in self.include_patterns)
                    ):
                        continue
                yield full


class Endpoint:
    """Represents a single API endpoint."""

    def __init__(self, path, method, handler):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.description = ""
        self.parameters = []
        self.responses = {}

    def to_dict(self):
        return {
            "path": self.path,
            "method": self.method,
            "handler": self.handler,
            "description": self.description,
            "parameters": self.parameters,
            "responses": self.responses
        }