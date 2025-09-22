import requests
url = "https://mcp-color-server.onrender.com/mcp"

# Probar tools/call directamente
payload = {
    "jsonrpc": "2.0", 
    "method": "tools/call", 
    "params": {
        "name": "hex_to_rgb",
        "arguments": {"hex_color": "FF0000"}
    }, 
    "id": 1
}

response = requests.post(url, json=payload)
print("Direct server test:", response.text)