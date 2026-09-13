# Contributing

Thank you for helping improve `apidocgen`! 

## Adding a New Framework Scanner

All scanners must conform to the `APIScanner` contract defined in `scanner/base.py`. 

### The Scanner Contract

1. Inherit from `scanner.base.APIScanner`.
2. Implement the `scan()` method. This method must discover endpoints and append `Endpoint` instances to `self.endpoints`.
3. Use `self._walk(exts=(...))` to traverse the project. It automatically respects user-configured `ignore` and `include` directives (e.g., skips `node_modules` and `venv`).

```python
from .base import APIScanner, Endpoint

class MyFrameworkScanner(APIScanner):
    def scan(self):
        for fp in self._walk(exts=(".myext",)):
            # parse the file to find routes...
            self.endpoints.append(Endpoint(
                path="/api/hello",
                method="GET",
                handler=fp
            ))
        return self.endpoints
```

4. Register your scanner in `scanner/registry.py` under `SUPPORTED_FRAMEWORKS` and provide an auto-detect function in `_DETECTORS`.

### Tests, Fixtures, and Golden-file Expectations

When adding or modifying a scanner, you must include a test fixture:
1. Add a tiny sample project using the framework under `tests/fixtures/<framework>_project`.
2. Do not pull in heavy actual dependencies (like massive `node_modules` or `.venv`); stub the files or imports just enough that the scanner can parse what it needs (e.g. a fake `package.json`, or a small `routes.py`).
3. Add a test in `tests/test_main.py` that runs the scanner against your fixture and asserts the resulting endpoints exactly match expectations (analogous to a golden-file approach, but checked via `assertIn`).

## Git Commit Style Guide

Please follow a structured commit style for all contributions. Avoid vague commit messages like "fix: fix" or "chore: chore". 

Use the Conventional Commits format to make history readable:

- `feat:` for new features (e.g., adding a scanner)
- `fix:` for bug fixes
- `docs:` for documentation updates
- `refactor:` for code changes that neither fix a bug nor add a feature
- `test:` for adding or fixing tests
- `chore:` for repository maintenance (e.g., dependency updates)

**Example:**
```
feat(scanner): add initial Laravel route scanner
fix(core): exclude node_modules from default python detection
```
