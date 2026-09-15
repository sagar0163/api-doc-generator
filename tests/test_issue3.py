import json
import os
import unittest

from openapi_spec_validator import validate

from main import scan_project
from generator.openapi import OpenAPIGenerator

FIXTURES_DIR = "tests/fixtures"

class TestIssue3GoldenFiles(unittest.TestCase):
    def _test_framework(self, framework):
        project_path = os.path.join(FIXTURES_DIR, f"{framework}_project")
        golden_file = os.path.join(FIXTURES_DIR, f"{framework}_expected.json")
        
        endpoints, schemas = scan_project(project_path, framework=framework, warn=lambda msg: None)
        
        gen = OpenAPIGenerator(title=f"{framework.capitalize()} Fixture API", version="1.0.0")
        for ep in endpoints:
            gen.add_endpoint(ep)
        for name, schema in schemas.items():
            gen.add_schema(name, schema)
            
        spec = gen.generate()
        
        # Validate OpenAPI spec
        validate(spec)
        
        # Compare with golden file
        with open(golden_file, "r") as f:
            expected_spec = json.load(f)
            
        self.assertEqual(spec, expected_spec)

    def test_fastapi(self):
        self._test_framework("fastapi")

    def test_flask(self):
        self._test_framework("flask")

    def test_express(self):
        self._test_framework("express")

if __name__ == "__main__":
    unittest.main()
