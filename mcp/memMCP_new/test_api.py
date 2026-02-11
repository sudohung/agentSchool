import requests

try:
    response = requests.get("http://127.0.0.1:8303/")
    print("Status:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)