"""Example generator for realistic JSON payloads"""

import random
import datetime
import uuid


class ExampleGenerator:
    """Generate realistic JSON examples based on variable names and types."""
    
    # Patterns to infer example values from variable names
    NAME_PATTERNS = {
        # Names
        r"(first|last|full)?_?name": "John Doe",
        r"(first|last)_?name": lambda: random.choice(["John", "Jane", "Alex", "Sam"]),
        r"email": "user@example.com",
        r"username": "johndoe123",
        r"password": "********",
        r"phone": lambda: f"+1{random.randint(1000000000, 9999999999)}",
        r"address": "123 Main Street",
        r"city": lambda: random.choice(["New York", "Los Angeles", "Chicago"]),
        r"country": lambda: random.choice(["USA", "UK", "Canada", "India"]),
        r"zipcode": lambda: str(random.randint(10000, 99999)),
        r"age": lambda: random.randint(18, 80),
        r"price": lambda: round(random.uniform(10, 1000), 2),
        r"amount": lambda: round(random.uniform(100, 50000), 2),
        r"quantity": lambda: random.randint(1, 100),
        r"id": lambda: str(uuid.uuid4()),
        r"user_?id": lambda: f"usr_{random.randint(1000, 9999)}",
        r"product_?id": lambda: f"prod_{random.randint(100, 999)}",
        r"order_?id": lambda: f"ord_{random.randint(10000, 99999)}",
        r"created_?at": lambda: datetime.datetime.now().isoformat(),
        r"updated_?at": lambda: datetime.datetime.now().isoformat(),
        r"date": lambda: datetime.date.today().isoformat(),
        r"timestamp": lambda: datetime.datetime.now().isoformat(),
        r"description": "Lorem ipsum dolor sit amet",
        r"title": "Sample Title",
        r"content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        r"status": lambda: random.choice(["active", "inactive", "pending"]),
        r"role": lambda: random.choice(["admin", "user", "moderator"]),
        r"is_?active": True,
        r"is_?verified": False,
        r"url": "https://example.com",
        r"image_?url": "https://via.placeholder.com/150",
        r"count": lambda: random.randint(0, 100),
        r"rate": lambda: round(random.uniform(1, 5), 1),
    }
    
    TYPE_EXAMPLES = {
        "str": "string",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "list": [],
        "dict": {},
    }
    
    def __init__(self):
        pass
    
    def generate_example(self, field_name, field_type=None):
        """Generate example value based on field name and type."""
        field_lower = field_name.lower()
        
        # Check name patterns
        for pattern, example in self.NAME_PATTERNS.items():
            import re
            if re.search(pattern, field_lower):
                if callable(example):
                    return example()
                return example
        
        # Fall back to type
        if field_type:
            return self.TYPE_EXAMPLES.get(field_type.lower(), "example")
        
        return "example_value"
    
    def generate_object_example(self, schema):
        """Generate example for entire object/schema."""
        example = {}
        
        for field_name, field_info in schema.items():
            if isinstance(field_info, dict):
                field_type = field_info.get("type")
                example[field_name] = self.generate_example(field_name, field_type)
            else:
                example[field_name] = self.generate_example(field_name)
        
        return example
    
    def generate_request_example(self, endpoint_info):
        """Generate example request body."""
        if "requestBody" in endpoint_info:
            schema = endpoint_info["requestBody"].get("schema", {})
            return self.generate_object_example(schema)
        return {}
    
    def generate_response_example(self, endpoint_info, status_code=200):
        """Generate example response."""
        if "responses" in endpoint_info:
            response = endpoint_info["responses"].get(str(status_code), {})
            if "content" in response:
                schema = response["content"].get("application/json", {}).get("schema", {})
                return self.generate_object_example(schema)
        return {"message": "Success"}
