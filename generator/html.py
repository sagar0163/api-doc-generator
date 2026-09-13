import json
import os

def generate_standalone_html(spec_dict, title="API Documentation"):
    """
    Generate a self-contained HTML file containing Swagger UI and the spec.
    """
    vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
    
    with open(os.path.join(vendor_dir, "swagger-ui.css"), "r", encoding="utf-8") as f:
        css = f.read()
        
    with open(os.path.join(vendor_dir, "swagger-ui-bundle.js"), "r", encoding="utf-8") as f:
        js = f.read()

    spec_json = json.dumps(spec_dict)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        /* swagger-ui.css */
        {css}
    </style>
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script>
        // swagger-ui-bundle.js
        {js}
    </script>
    <script>
        window.onload = function() {{
            const spec = {spec_json};
            window.ui = SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>"""
