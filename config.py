"""Configuration handling for the API doc generator.

``api-doc.yaml`` at the project root (or passed via ``--config``) controls
scanning.  CLI flags always win over config values.
"""

import json
import os


DEFAULT_CONFIG = {
    "framework": "auto",
    "include": [],
    "ignore": [".git", "node_modules", "venv", "__pycache__", "dist"],
    "output": "api-docs.json",
    "server": {"url": "http://localhost:3000", "description": None},
    "ai": {
        "enabled": False,
        "provider": "openai",
        "api_key_env": "OPENAI_API_KEY",
        "model": "gpt-4",
        "fields": ["description", "example", "operationSummary"]
    },
}


def _read_file(path):
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    except OSError:
        return None


def _load_yaml(text):
    try:
        import yaml
    except ImportError:
        raise RuntimeError(
            "PyYAML is required to read YAML config files. "
            "Install it (pip install pyyaml) or use a .json config."
        )
    try:
        return yaml.safe_load(text) or {}
    except Exception as e:
        raise ValueError(f"invalid YAML in config: {e}")


def _load_json(text):
    try:
        return json.loads(text) or {}
    except Exception as e:
        raise ValueError(f"invalid JSON in config: {e}")


def load_config(path=None):
    """Load a config file and merge it over defaults.

    If ``path`` is None, look for ``api-doc.yaml`` / ``api-doc.yml`` /
    ``api-doc.json`` in the current directory.  Returns a dict that always
    contains every ``DEFAULT_CONFIG`` key.
    """
    if path is None:
        for candidate in ("api-doc.yaml", "api-doc.yml", "api-doc.json"):
            if os.path.exists(candidate):
                path = candidate
                break

    config = {}
    if path is not None:
        if not os.path.exists(path):
            raise ValueError(f"config file not found: {path}")
        text = _read_file(path)
        if text is None:
            raise ValueError(f"config file not readable: {path}")
        ext = os.path.splitext(path)[1].lower()
        raw = _load_yaml(text) if ext in (".yaml", ".yml") else _load_json(text)
        config = raw

    merged = dict(DEFAULT_CONFIG)
    merged.update({k: v for k, v in config.items() if v is not None})

    # ignore is additive with the built-in defaults.
    extra = config.get("ignore")
    if isinstance(extra, list):
        merged["ignore"] = list(dict.fromkeys(
            list(DEFAULT_CONFIG["ignore"]) + [i for i in extra]
        ))

    if "server" in config and isinstance(config["server"], dict):
        merged["server"] = {**DEFAULT_CONFIG["server"], **config["server"]}

    if "ai" in config and isinstance(config["ai"], dict):
        merged["ai"] = {**DEFAULT_CONFIG["ai"], **config["ai"]}

    if "framework" in config and config["framework"] is not None:
        merged["framework"] = str(config["framework"])

    return merged