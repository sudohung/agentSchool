import requests
import json

# Test POST request
url = "http://localhost:8303/memories"
data = {
    "title": "API测试",
    "content": "这是一个API测试记忆",
    "type": "business_knowledge"
}

try:
    response = requests.post(url, json=data)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)