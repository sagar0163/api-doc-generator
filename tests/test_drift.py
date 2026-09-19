import pytest
import os
import json
from unittest.mock import patch, mock_open

from drift import compute_diff, filter_spec, check_drift

def test_compute_diff():
    old = {
        "paths": {
            "/a": {"get": {}},
            "/b": {"post": {}}
        }
    }
    new = {
        "paths": {
            "/a": {"get": {}, "post": {}},
            "/c": {"get": {}}
        }
    }
    report = compute_diff(old, new)
    assert "  + added method: POST /a" in report
    assert "- removed path: /b" in report
    assert "+ added path: /c" in report

def test_filter_spec():
    spec = {
        "info": {"description": "foo", "title": "bar"},
        "paths": {
            "/a": {
                "get": {"description": "baz", "responses": {"200": {"description": "ok"}}}
            }
        }
    }
    filtered = filter_spec(spec, ["description"])
    assert "description" not in filtered["info"]
    assert "title" in filtered["info"]
    assert "description" not in filtered["paths"]["/a"]["get"]
    assert "description" not in filtered["paths"]["/a"]["get"]["responses"]["200"]

    filtered_dot = filter_spec(spec, ["info.description"])
    assert "description" not in filtered_dot["info"]
    assert "description" in filtered_dot["paths"]["/a"]["get"]

def test_check_drift():
    old_json = json.dumps({"info": {"title": "A"}})
    new_json = json.dumps({"info": {"title": "B"}})
    
    is_drift, diff = check_drift(old_json, new_json, [], "api-docs.json")
    assert is_drift
    assert "- info changed" in diff

    is_drift, diff = check_drift(old_json, old_json, [], "api-docs.json")
    assert not is_drift

