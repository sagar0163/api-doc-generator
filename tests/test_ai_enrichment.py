import pytest
from generator.ai import AIEnricher
import os

def test_ai_enricher_no_key_fails(monkeypatch):
    config = {"ai": {"enabled": True, "api_key_env": "MISSING_KEY_ENV"}}
    if "MISSING_KEY_ENV" in os.environ:
        monkeypatch.delenv("MISSING_KEY_ENV")
    
    enricher = AIEnricher(config)
    spec = {"paths": {"/": {"get": {}}}}
    
    with pytest.raises(SystemExit):
        enricher.enrich(spec)

def test_ai_enricher_success(monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "TEST_KEY")
    config = {"ai": {"enabled": True, "api_key_env": "TEST_OPENAI_KEY", "fields": ["description"]}}
    enricher = AIEnricher(config)
    spec = {"paths": {"/api": {"get": {}}}}
    
    new_spec = enricher.enrich(spec)
    assert new_spec["paths"]["/api"]["get"]["description"].startswith("> _AI-generated_")
    assert new_spec["paths"]["/api"]["get"]["x-aidoc-generated"] is True

def test_ai_enricher_disabled():
    config = {"ai": {"enabled": False}}
    enricher = AIEnricher(config)
    spec = {"paths": {"/api": {"get": {}}}}
    
    new_spec = enricher.enrich(spec)
    assert "description" not in new_spec["paths"]["/api"]["get"]

def test_ai_enricher_provider_failure(monkeypatch):
    monkeypatch.setenv("FAIL_OPENAI_KEY", "FAIL_KEY")
    config = {"ai": {"enabled": True, "api_key_env": "FAIL_OPENAI_KEY"}}
    enricher = AIEnricher(config)
    spec = {"paths": {"/api": {"get": {}}}}
    
    with pytest.raises(Exception, match="Provider response failure"):
        enricher.enrich(spec)
