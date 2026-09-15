"""Drift detection for generated API specs (issue #4).

A "drift" is any difference between the spec committed on disk and a spec
freshly regenerated from the codebase.  ``detect_drift()`` compares two
decoded spec dicts and returns a structured change report; ``remove_ignored()``
drops configured noisiness (e.g. ``info.description``, example values) before
comparison; ``render_drift()`` turns a change report into the deterministic,
diffable text printed by ``apidocgen check`` / ``apidocgen diff``.
"""

import json
import re
from typing import Any, Dict, Iterable, Iterator, List, Tuple

#: A change triple: (dot-path, old_value, new_value).  old_value is None for
#: additions, new_value is None for removals.
Change = Tuple[str, Any, Any]


def _match_path(path: str, pattern: str) -> bool:
    """Return True if ``path`` matches ``pattern``.

    ``*`` matches exactly one dot-segment, ``**`` matches any number of
    segments (including none).  Without a star the match is exact, so dot-
    paths that contain no wildcard cannot over-match.
    """
    if "*" not in pattern:
        return path == pattern
    regex = pattern.replace(".", r"\.")
    regex = regex.replace("**", "\x00DOUBLE\x00")
    regex = regex.replace("*", r"[^.]+")
    regex = regex.replace("\x00DOUBLE\x00", ".*")
    return re.fullmatch(regex, path) is not None


def _remove_ignored_recursive(data: Any, current_path: str, patterns: List[str]) -> Any:
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            path = "{}.{}".format(current_path, k) if current_path else str(k)
            if any(_match_path(path, p) for p in patterns):
                continue
            out[k] = _remove_ignored_recursive(v, path, patterns)
        return out
    if isinstance(data, list):
        return [_remove_ignored_recursive(v, current_path, patterns) for v in data]
    return data


def remove_ignored(spec: Dict[str, Any], ignored_paths: Iterable[str]) -> Dict[str, Any]:
    """Return ``spec`` with dot-paths matching ``ignored_paths`` pruned.

    Used before comparison so configured noise (``info.description``,
    example values) never trips drift detection.  List elements keep their
    container's path, so ``**.example`` still matches keys nested under
    list items.
    """
    patterns = [str(p) for p in (ignored_paths or [])]
    if not patterns:
        return spec
    return _remove_ignored_recursive(spec, "", patterns)


def iter_item_changes(old_item: Any, new_item: Any, path: str) -> Iterator[Change]:
    """Yield (path, old, new) for every leaf/value that differs.

    ``None`` on the old side marks an addition, ``None`` on the new side a
    removal.  Lists are compared positionally; a length mismatch is reported
    once at the list path itself.
    """
    if type(old_item) != type(new_item):
        yield path, old_item, new_item
        return
    if isinstance(old_item, dict):
        for k in sorted(set(old_item) | set(new_item)):
            child = "{}.{}".format(path, k)
            if k not in old_item:
                yield child, None, new_item[k]
            elif k not in new_item:
                yield child, old_item[k], None
            else:
                yield from iter_item_changes(old_item[k], new_item[k], child)
    elif isinstance(old_item, list):
        if len(old_item) != len(new_item):
            yield path, old_item, new_item
            return
        for i, (o, n) in enumerate(zip(old_item, new_item)):
            yield from iter_item_changes(o, n, "{}[{}]".format(path, i))
    elif old_item != new_item:
        yield path, old_item, new_item


def detect_drift(committed: Dict[str, Any], fresh: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two specs and return a structured change report.

    ``committed`` is the spec currently on disk; ``fresh`` is the spec just
    regenerated from the codebase.  "added" means present in ``fresh`` but
    not ``committed`` (a new endpoint in the code that is undocumented);
    "removed" is the reverse.  Pass both specs through :func:`remove_ignored`
    first if ``drift.ignore`` is configured.

    Return value::

        {"paths": {
            "/users/": {"type": "added" | "removed"},
            "/user/{id}": {"type": "changed", "diffs": [Change, ...]},
         },
         "other": {"type": "changed", "diffs": [Change, ...]}}
    """
    changes: Dict[str, Any] = {}
    old_paths = committed.get("paths") or {}
    new_paths = fresh.get("paths") or {}

    path_changes: Dict[str, Dict[str, Any]] = {}
    for p in sorted(set(old_paths) | set(new_paths)):
        if p not in old_paths:
            path_changes[p] = {"type": "added"}
        elif p not in new_paths:
            path_changes[p] = {"type": "removed"}
        else:
            diffs = list(
                iter_item_changes(old_paths[p], new_paths[p], "paths.{}".format(p))
            )
            if diffs:
                path_changes[p] = {"type": "changed", "diffs": diffs}
    if path_changes:
        changes["paths"] = path_changes

    other: List[Change] = []
    for k in sorted(set(committed) | set(fresh)):
        if k == "paths":
            continue
        if k not in committed:
            other.append((k, None, fresh[k]))
        elif k not in fresh:
            other.append((k, committed[k], None))
        else:
            other.extend(iter_item_changes(committed[k], fresh[k], k))
    if other:
        changes["other"] = {"type": "changed", "diffs": other}

    return changes


def _fmt(value: Any, limit: int = 60) -> str:
    """Deterministic single-line representation of a spec value."""
    if isinstance(value, dict):
        inner = ", ".join(
            "{}={}".format(k, _fmt(v, limit)) for k, v in sorted(value.items())
        )
        kind_open, kind_close = "{", "}"
    elif isinstance(value, (list, tuple)):
        inner = ", ".join(_fmt(v, limit) for v in value)
        kind_open, kind_close = "[", "]"
    elif isinstance(value, str):
        return value if len(value) <= limit else value[: limit - 3] + "..."
    elif value is None or isinstance(value, bool):
        return json.dumps(value)
    else:
        return str(value)
    if len(inner) > limit:
        inner = inner[: limit - 3] + "..."
    return "{}{}{}".format(kind_open, inner, kind_close)


def _format_value_change(path: str, old: Any, new: Any) -> str:
    if old is None:
        return "+ {}: {}".format(path, _fmt(new))
    if new is None:
        return "- {}: {}".format(path, _fmt(old))
    return "~ {}: {} -> {}".format(path, _fmt(old), _fmt(new))


def render_drift(changes: Dict[str, Any], detail: bool = False) -> str:
    """Render a change report as deterministic, diffable text.

    With ``detail=False`` (the ``check`` report) only path-level changes are
    listed - concise enough for a fast yes/no.  With ``detail=True`` (the
    ``diff`` output) item-level changes are shown under each changed path.
    """
    if not changes:
        return "No drift detected."

    n_items = len(changes.get("other", {}).get("diffs", []))
    lines = [
        "Drift detected: {} path-level, {} item-level change(s)".format(
            len(changes.get("paths", {})), n_items
        )
    ]

    if "other" in changes:
        for path, old, new in changes["other"]["diffs"]:
            lines.append("  " + _format_value_change(path, old, new))

    if "paths" in changes:
        for p, change in sorted(changes["paths"].items()):
            if change["type"] == "added":
                lines.append("  + {} (added)".format(p))
            elif change["type"] == "removed":
                lines.append("  - {} (removed)".format(p))
            else:
                lines.append("  ~ {} (changed)".format(p))
                if detail:
                    base = "paths.{}".format(p)
                    for path, old, new in change["diffs"]:
                        rel = path[len(base):].lstrip(".")
                        lines.append("      " + _format_value_change(rel, old, new))

    return "\n".join(lines)