import os
import json
import urllib.request
import urllib.error

def enrich_spec(spec, ai_cfg):
    provider = ai_cfg.get("provider", "openai")
    api_key_env = ai_cfg.get("api_key_env", "OPENAI_API_KEY")
    model = ai_cfg.get("model", "gpt-3.5-turbo")
    fields = ai_cfg.get("fields", ["description", "example", "operationSummary"])
    
    api_key = os.environ.get(api_key_env)
    if not api_key and provider != "ollama":
        print(f"AI Enrichment bypassed: No API key found in environment variable '{api_key_env}'.")
        return spec

    # Collect all items to enrich
    to_enrich = []
    
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            to_enrich.append({
                "type": "operation",
                "path": path,
                "method": method,
                "summary": operation.get("summary", ""),
                "description": operation.get("description", ""),
                "ref": operation
            })

    schemas = spec.get("components", {}).get("schemas", {})
    for schema_name, schema_def in schemas.items():
        if not isinstance(schema_def, dict):
            continue
        to_enrich.append({
            "type": "schema",
            "name": schema_name,
            "ref": schema_def
        })
        
    if not to_enrich:
        return spec

    # Build prompt
    prompt = (
        "You are an API documentation generator. I will provide a list of API operations and schemas. "
        "For each item, provide a JSON object with keys 'description', 'example', and 'operationSummary' (only if it's an operation). "
        "The 'example' should be a valid JSON representation or snippet. "
        "Reply with ONLY a JSON array of objects in the EXACT same order. Do not wrap it in markdown block quotes, just raw JSON array.\n\n"
    )
    for i, item in enumerate(to_enrich):
        prompt += f"Item {i}:\nType: {item['type']}\n"
        if item['type'] == 'operation':
            prompt += f"Path: {item['path']}\nMethod: {item['method']}\nCurrent Summary: {item['summary']}\nCurrent Description: {item['description']}\n"
        else:
            prompt += f"Schema Name: {item['name']}\n"
        prompt += "\n"
        
    try:
        response_json = _call_llm(provider, model, api_key, prompt)
        
        # Strip markdown if present
        if response_json.startswith("```json"):
            response_json = response_json[7:-3]
        elif response_json.startswith("```"):
            response_json = response_json[3:-3]
        response_json = response_json.strip()

        enriched_data = json.loads(response_json)
        if not isinstance(enriched_data, list) or len(enriched_data) != len(to_enrich):
            raise ValueError(f"Invalid response format or count mismatch (expected {len(to_enrich)} items, got {len(enriched_data) if isinstance(enriched_data, list) else type(enriched_data)})")
    except Exception as e:
        raise RuntimeError(f"Provider response failure: {e}")
        
    # Merge back
    for i, item in enumerate(to_enrich):
        data = enriched_data[i]
        target = item["ref"]
        
        # We only mark the object as AI-generated if we actually changed it
        changed = False
        
        if "description" in fields and data.get("description"):
            target["description"] = f"> _AI-generated_\n{data['description']}"
            changed = True
            
        if "example" in fields and data.get("example"):
            target["example"] = data['example']
            changed = True
            
        if "operationSummary" in fields and item["type"] == "operation" and data.get("operationSummary"):
            target["summary"] = f"{data['operationSummary']} (AI)"
            changed = True
            
        if changed:
            target["x-aidoc-generated"] = True

    return spec

def _call_llm(provider, model, api_key, prompt):
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
    elif provider == "ollama":
        url = "http://localhost:11434/api/chat"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")

    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if provider == "openai":
                return result["choices"][0]["message"]["content"]
            elif provider == "anthropic":
                return result["content"][0]["text"]
            elif provider == "ollama":
                return result["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {body}")
