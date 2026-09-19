def _remove_ignored_keys(data, ignore_keys):
    if not isinstance(data, dict):
        return
    for k in list(data.keys()):
        if k in ignore_keys:
            del data[k]
        else:
            if isinstance(data[k], dict):
                _remove_ignored_keys(data[k], ignore_keys)
            elif isinstance(data[k], list):
                for item in data[k]:
                    _remove_ignored_keys(item, ignore_keys)

def filter_spec(spec_dict, ignores):
    """Deep copy and filter ignored keys (like description, example, or specific paths like info.description)."""
    import copy
    import json
    
    # Fast deepcopy
    d = json.loads(json.dumps(spec_dict))
    
    # Handle flat ignore keys
    flat_ignores = set()
    for ig in ignores:
        if '.' in ig:
            parts = ig.split('.')
            curr = d
            valid = True
            for part in parts[:-1]:
                if part in curr and isinstance(curr[part], dict):
                    curr = curr[part]
                else:
                    valid = False
                    break
            if valid and parts[-1] in curr:
                del curr[parts[-1]]
        else:
            flat_ignores.add(ig)
            
    if flat_ignores:
        _remove_ignored_keys(d, flat_ignores)
        
    return d

def compute_diff(old_spec, new_spec):
    """Compute path-level and item-level drift."""
    diff_report = []
    
    # Info
    if old_spec.get('info') != new_spec.get('info'):
        diff_report.append("- info changed")
        
    old_paths = old_spec.get('paths', {})
    new_paths = new_spec.get('paths', {})
    
    all_paths = set(old_paths.keys()) | set(new_paths.keys())
    for path in sorted(all_paths):
        if path not in old_paths:
            diff_report.append(f"+ added path: {path}")
        elif path not in new_paths:
            diff_report.append(f"- removed path: {path}")
        else:
            old_methods = old_paths[path]
            new_methods = new_paths[path]
            all_methods = set(old_methods.keys()) | set(new_methods.keys())
            for method in sorted(all_methods):
                if method not in old_methods:
                    diff_report.append(f"  + added method: {method.upper()} {path}")
                elif method not in new_methods:
                    diff_report.append(f"  - removed method: {method.upper()} {path}")
                else:
                    if old_methods[method] != new_methods[method]:
                        diff_report.append(f"  ~ changed method: {method.upper()} {path}")
                        
    old_schemas = old_spec.get('components', {}).get('schemas', {})
    new_schemas = new_spec.get('components', {}).get('schemas', {})
    all_schemas = set(old_schemas.keys()) | set(new_schemas.keys())
    for schema in sorted(all_schemas):
        if schema not in old_schemas:
            diff_report.append(f"+ added schema: {schema}")
        elif schema not in new_schemas:
            diff_report.append(f"- removed schema: {schema}")
        else:
            if old_schemas[schema] != new_schemas[schema]:
                diff_report.append(f"  ~ changed schema: {schema}")
                
    return diff_report

def check_drift(old_payload, new_payload, ignores, output_ext):
    import json
    try:
        if output_ext in (".yaml", ".yml"):
            import yaml
            new_spec = yaml.safe_load(new_payload)
            old_spec = yaml.safe_load(old_payload)
        else:
            new_spec = json.loads(new_payload)
            old_spec = json.loads(old_payload)
    except Exception as e:
        return True, [f"Error parsing specs for diff: {e}"]
        
    if ignores:
        old_spec = filter_spec(old_spec, ignores)
        new_spec = filter_spec(new_spec, ignores)

    diff_report = compute_diff(old_spec, new_spec)
    
    if output_ext in (".yaml", ".yml"):
        import yaml
        filtered_payload = yaml.dump(new_spec, default_flow_style=False, sort_keys=True)
        filtered_committed = yaml.dump(old_spec, default_flow_style=False, sort_keys=True)
    else:
        filtered_payload = json.dumps(new_spec, indent=2, sort_keys=True)
        filtered_committed = json.dumps(old_spec, indent=2, sort_keys=True)
        
    is_drift = filtered_payload != filtered_committed
    return is_drift, diff_report
