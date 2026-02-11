import requests
import json

# Test different request formats
test_cases = [
    {
        "name": "Minimal required fields",
        "data": {
            "title": "Test Title",
            "content": "Test Content"
        }
    },
    {
        "name": "All fields",
        "data": {
            "title": "Complete Test",
            "content": "Complete test content",
            "type": "business_knowledge",
            "category": "Testing",
            "tags": ["api", "test"],
            "language": None,
            "source": "debug_script"
        }
    },
    {
        "name": "With code snippet type",
        "data": {
            "title": "Python Code Test",
            "content": "print('hello world')",
            "type": "code_snippet",
            "language": "python"
        }
    }
]

url = "http://localhost:8303/memories"

for test_case in test_cases:
    print(f"\n=== Testing: {test_case['name']} ===")
    try:
        response = requests.post(url, json=test_case["data"])
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")