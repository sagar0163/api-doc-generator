import json
import os
from main import scan_project
from generator.openapi import OpenAPIGenerator

for framework in ["fastapi", "flask", "express"]:
    project_path = f"tests/fixtures/{framework}_project"
    if not os.path.exists(project_path):
        continue
    endpoints, schemas = scan_project(project_path, framework=framework)
    
    gen = OpenAPIGenerator(title=f"{framework.capitalize()} Fixture API", version="1.0.0")
    for ep in endpoints:
        gen.add_endpoint(ep)
    for name, schema in schemas.items():
        gen.add_schema(name, schema)
        
    spec = gen.generate()
    with open(f"tests/fixtures/{framework}_expected.json", "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Generated tests/fixtures/{framework}_expected.json")
