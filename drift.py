import re
from typing import Any, Dict, List, Set, Tuple

def _match_path(path: str, pattern: str) -> bool:
    """Check if a dot-path matches a pattern with * or **."""
    if '*' in pattern:
        regex = pattern.replace('.', r'\.')
        regex = regex.replace('**', '___DOUBLE___')
        regex = regex.replace('*', '[^.]+')
        regex = regex.replace('___DOUBLE___', '.*')
        return re.fullmatch(regex, path) is not None
    return path == pattern

def _remove_ignored_recursive(data: Any, current_path: str, ignored_patterns: List[str]) -> Any:
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            path = f"{current_path}.{k}" if current_path else k
            if any(_match_path(path, p) for p in ignored_patterns):
                continue
            new_dict[k] = _remove_ignored_recursive(v, path, ignored_patterns)
        return new_dict
    elif isinstance(data, list):
        return [_remove_ignored_recursive(v, current_path, ignored_patterns) for v in data]
    else:
        return data

def remove_ignored(spec: dict, ignored_paths: List[str]) -> dict:
    """Remove ignored paths from the spec dictionary."""
    if not ignored_paths:
        return spec
    return _remove_ignored_recursive(spec, "", ignored_paths)

def iter_item_changes(old_item: Any, new_item: Any, path: str) -> Tuple[str, Any, Any]:
    """Yield changes between two items."""
    if type(old_item) != type(new_item):
        yield path, old_item, new_item
        return
        
    if isinstance(old_item, dict):
        for k in set(old_item.keys()) | set(new_item.keys()):
            new_path = f"{path}.{k}"
            if k not in old_item:
                yield new_path, old_item[k], None
            elif k not in new_item:
                yield new_path, None, new_item[k]
            else:
                yield from iter_item_changes(old_item[k], new_item[k], new_path)
    elif isinstance(old_item, list):
        if len(old_item) != len(new_item):
            yield path, old_item, new_item
        else:
            for i, (o, n) in enumerate(zip(old_item, new_item)):
                yield from iter_item_changes(o, n, f"{path}[{i}]")
    else:
        if old_item != new_item:
            yield path, old_item, new_item

def detect_drift(old_spec: dict, new_spec: dict) -> dict:
    """Detect differences between two specs."""
    changes = {}
    
    # Check paths
    old_paths = old_spec.get('paths', {})
    new_paths = new_spec.get('paths', {})
    
    path_changes = {}
    for p in set(old_paths.keys()) | set(new_paths.keys()):
        if p not in old_paths:
            path_changes[p] = {'type': 'removed'}
        elif p not in new_paths:
            path_changes[p] = {'type': 'added'}
        else:
            diffs = list(iter_item_changes(old_paths[p], new_paths[p], f"paths.{p}"))
            if diffs:
                path_changes[p] = {'type': 'changed', 'diffs': diffs}
    
    if path_changes:
        changes['paths'] = path_changes
        
    # Check other top-level keys
    other_diffs = []
    for k in set(old_spec.keys()) | set(new_spec.keys()):
        if k == 'paths':
            continue
        if k not in old_spec:
            other_diffs.append((k, old_spec[k], None))
        elif k not in new_spec:
            other_diffs.append((k, None, new_spec[k]))
        else:
            other_diffs.extend(iter_item_changes(old_spec[k], new_spec[k], k))
            
    if other_diffs:
        changes['other'] = {'type': 'changed', 'diffs': other_diffs}
        
    return changes

def render_drift(changes: dict) -> str:
    """Render a drift report."""
    if not changes:
        return "No drift detected."
    
    lines = ["Drift detected:"]
    
    if 'other' in changes:
        for diff in changes['other']['diffs']:
            lines.append(f"  ~ {diff[0]}: {diff[1]} -> {diff[2]}")
            
    if 'paths' in changes:
        for p, change in sorted(changes['paths'].items()):
            if change['type'] == 'added':
                lines.append(f"  + {p} (added)")
            elif change['type'] == 'removed':
                lines.append(f"  - {p} (removed)")
            else:
                lines.append(f"  ~ {p} (changed)")
                for diff in change['diffs']:
                    lines.append(f"    - {diff[0]}: {diff[1]} -> {diff[2]}")
                    
    return "\n".join(lines)
