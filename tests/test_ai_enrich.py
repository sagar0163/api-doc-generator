import unittest
from unittest.mock import patch
import ai_enrich

class TestAIEnrich(unittest.TestCase):

    def test_enrich_spec_no_key(self):
        spec = {"paths": {"/a": {"get": {"summary": "test"}}}}
        cfg = {"provider": "openai", "api_key_env": "MISSING_ENV_KEY"}
        
        enriched = ai_enrich.enrich_spec(spec, cfg)
        
        self.assertEqual(enriched["paths"]["/a"]["get"]["summary"], "test")
        self.assertNotIn("x-aidoc-generated", enriched["paths"]["/a"]["get"])

    @patch("ai_enrich._call_llm")
    def test_enrich_spec_with_key(self, mock_call):
        spec = {
            "paths": {
                "/a": {
                    "get": {"summary": "old summary"}
                }
            },
            "components": {
                "schemas": {
                    "User": {"type": "object"}
                }
            }
        }
        cfg = {
            "provider": "openai",
            "api_key_env": "TEST_KEY",
            "fields": ["description", "example", "operationSummary"]
        }
        
        import os
        os.environ["TEST_KEY"] = "fake-key"
        
        mock_call.return_value = '''[
            {"description": "A test operation", "example": "{}", "operationSummary": "Test Op"},
            {"description": "A user schema", "example": "{\\"id\\": 1}", "operationSummary": null}
        ]'''
        
        enriched = ai_enrich.enrich_spec(spec, cfg)
        
        # Check operation
        op = enriched["paths"]["/a"]["get"]
        self.assertEqual(op["summary"], "Test Op (AI)")
        self.assertEqual(op["description"], "> _AI-generated_\nA test operation")
        self.assertTrue(op["x-aidoc-generated"])
        
        # Check schema
        schema = enriched["components"]["schemas"]["User"]
        self.assertEqual(schema["description"], "> _AI-generated_\nA user schema")
        self.assertEqual(schema["example"], '{"id": 1}')
        self.assertTrue(schema["x-aidoc-generated"])

if __name__ == "__main__":
    unittest.main()
