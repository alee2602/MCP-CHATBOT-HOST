import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

REMOTE_SERVER = "https://mcp-color-server.onrender.com/mcp"

class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/mcp':
            # Read requests from chatbot
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"Request from chatbot: {post_data.decode('utf-8')}")
            
            try:
                # Forward to remote server
                response = requests.post(REMOTE_SERVER, data=post_data, headers={'Content-Type': 'application/json'})
                
                print(f"Response from remote: {response.text}")
                
                # Get response from server
                self.send_response(response.status_code)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response.content)
                
            except Exception as e:
                error_response = {"jsonrpc": "2.0", "id": 1, "error": {"code": -1, "message": str(e)}}
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())

if __name__ == "__main__":
    server = HTTPServer(('localhost', 8080), ProxyHandler)
    print("MCP Proxy running on http://localhost:8080")
    print("Configure your chatbot to use: http://localhost:8080/mcp")
    server.serve_forever()