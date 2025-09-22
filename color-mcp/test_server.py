import requests
import json

url = "https://mcp-color-server.onrender.com/mcp"
payload = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"JSON Response: {json.dumps(data, indent=2)}")