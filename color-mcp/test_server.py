import requests
import time

url = "https://mcp-color-server.onrender.com/mcp"

print("Generando tráfico MCP...")

# Múltiples llamadas para generar tráfico visible
for i in range(5):
    # tools/list call
    payload1 = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": i*2+1}
    response1 = requests.post(url, json=payload1)
    print(f"tools/list #{i+1}: {response1.status_code}")
    
    time.sleep(2)
    
    # tools/call
    payload2 = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "random_color", "arguments": {}}, "id": i*2+2}
    response2 = requests.post(url, json=payload2)
    print(f"tools/call #{i+1}: {response2.status_code}")
    
    time.sleep(2)

print("Tráfico generado. Revisa Wireshark.")