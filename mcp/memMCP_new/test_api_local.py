import urllib.request
import json

# Test the API
try:
    # Test health check
    with urllib.request.urlopen('http://127.0.0.1:8303/') as response:
        data = response.read().decode('utf-8')
        print("Health check:", data)
    
    # Test POST request
    data = {
        "title": "API测试",
        "content": "这是一个API测试记忆"
    }
    req = urllib.request.Request(
        'http://127.0.0.1:8303/memories',
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print("POST result:", result)
        
except Exception as e:
    print("Error:", e)