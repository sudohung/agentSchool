import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:8304/') as response:
        data = response.read().decode('utf-8')
        print("Success:", data)
except Exception as e:
    print("Error:", e)