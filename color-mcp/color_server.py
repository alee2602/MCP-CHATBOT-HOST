import asyncio
import json
import os
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Importar MCP
from fastmcp import FastMCP

# Crear servidor MCP
mcp = FastMCP("ColorTools")

# === HERRAMIENTAS MCP ORIGINALES ===

@mcp.tool()
def hex_to_rgb(hex_color: str) -> str:
    """Convert HEX color to RGB values"""
    log_mcp_call("hex_to_rgb", {"hex_color": hex_color})
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return "Error: HEX color must be 6 characters long (e.g., #FF0000 or FF0000)"
        
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        result = f"HEX #{hex_color.upper()} = RGB({rgb[0]}, {rgb[1]}, {rgb[2]})"
        log_mcp_response("hex_to_rgb", result)
        return result
    except ValueError:
        error = "Error: Invalid HEX color format. Use format like #FF0000 or FF0000"
        log_mcp_response("hex_to_rgb", error)
        return error

@mcp.tool()
def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to HEX color"""
    log_mcp_call("rgb_to_hex", {"r": r, "g": g, "b": b})
    try:
        if not all(0 <= val <= 255 for val in [r, g, b]):
            error = "Error: RGB values must be between 0 and 255"
            log_mcp_response("rgb_to_hex", error)
            return error
        
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        result = f"RGB({r}, {g}, {b}) = HEX {hex_color}"
        log_mcp_response("rgb_to_hex", result)
        return result
    except Exception as e:
        error = f"Error: {str(e)}"
        log_mcp_response("rgb_to_hex", error)
        return error

@mcp.tool()
def random_color() -> str:
    """Generate a random color in both HEX and RGB formats"""
    log_mcp_call("random_color", {})
    import random
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    hex_color = f"#{r:02X}{g:02X}{b:02X}"
    result = f"Random Color: HEX {hex_color} | RGB({r}, {g}, {b})"
    log_mcp_response("random_color", result)
    return result

@mcp.tool()
def color_palette(base_color: str, palette_type: str = "complementary") -> str:
    """Generate color palette based on a base color"""
    log_mcp_call("color_palette", {"base_color": base_color, "palette_type": palette_type})
    try:
        import colorsys
        base_color = base_color.lstrip('#')
        if len(base_color) != 6:
            error = "Error: Base color must be in HEX format (e.g., #FF0000)"
            log_mcp_response("color_palette", error)
            return error
        
        # Convert to RGB then HSV
        rgb = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = [x/255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        colors = [f"#{base_color.upper()} (base)"]
        
        if palette_type == "complementary":
            comp_h = (h + 0.5) % 1.0
            comp_rgb = colorsys.hsv_to_rgb(comp_h, s, v)
            comp_rgb = tuple(int(x * 255) for x in comp_rgb)
            colors.append(f"#{comp_rgb[0]:02X}{comp_rgb[1]:02X}{comp_rgb[2]:02X} (complementary)")
            
        elif palette_type == "triadic":
            for offset in [1/3, 2/3]:
                tri_h = (h + offset) % 1.0
                tri_rgb = colorsys.hsv_to_rgb(tri_h, s, v)
                tri_rgb = tuple(int(x * 255) for x in tri_rgb)
                colors.append(f"#{tri_rgb[0]:02X}{tri_rgb[1]:02X}{tri_rgb[2]:02X} (triadic)")
                
        elif palette_type == "analogous":
            for offset in [-30/360, 30/360]:
                ana_h = (h + offset) % 1.0
                ana_rgb = colorsys.hsv_to_rgb(ana_h, s, v)
                ana_rgb = tuple(int(x * 255) for x in ana_rgb)
                colors.append(f"#{ana_rgb[0]:02X}{ana_rgb[1]:02X}{ana_rgb[2]:02X} (analogous)")
        
        result = f"{palette_type.capitalize()} Palette:\n" + "\n".join(colors)
        log_mcp_response("color_palette", result)
        return result
    except Exception as e:
        error = f"Error: {str(e)}"
        log_mcp_response("color_palette", error)
        return error

# === LOGGING PARA ANÁLISIS ===

mcp_log = []

def log_mcp_call(method, params):
    """Log MCP method call"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "type": "request",
        "method": method,
        "params": params,
        "protocol": "MCP-JSON-RPC"
    }
    mcp_log.append(log_entry)
    print(f"📞 MCP CALL: {method} - {params}")

def log_mcp_response(method, result):
    """Log MCP method response"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "type": "response", 
        "method": method,
        "result": result,
        "protocol": "MCP-JSON-RPC"
    }
    mcp_log.append(log_entry)
    print(f"✅ MCP RESPONSE: {method} - {result[:50]}...")

# === SERVIDOR HTTP PARA ANÁLISIS ===

class AnalysisHandler(BaseHTTPRequestHandler):
    """HTTP handler para análisis con Wireshark"""
    
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/':
            self.send_dashboard()
        elif path == '/logs':
            self.send_logs()
        elif path == '/api/hex-to-rgb':
            params = parse_qs(parsed_url.query)
            hex_color = params.get('hex', [''])[0]
            result = hex_to_rgb(hex_color)
            self.send_json_response({"result": result, "method": "hex_to_rgb"})
        elif path == '/api/random-color':
            result = random_color()
            self.send_json_response({"result": result, "method": "random_color"})
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle JSON-RPC style requests para simular MCP"""
        if self.path == '/mcp':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode('utf-8'))
                method = request_data.get('method')
                params = request_data.get('params', {})
                request_id = request_data.get('id', 1)
                
                # Simular llamada MCP
                if method == 'hex_to_rgb':
                    result = hex_to_rgb(params.get('hex_color', ''))
                elif method == 'rgb_to_hex':
                    result = rgb_to_hex(params.get('r', 0), params.get('g', 0), params.get('b', 0))
                elif method == 'random_color':
                    result = random_color()
                else:
                    result = f"Unknown method: {method}"
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                
                self.send_json_response(response)
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": 1,
                    "error": {"code": -1, "message": str(e)}
                }
                self.send_json_response(error_response)
    
    def send_dashboard(self):
        """Send HTML dashboard"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Color MCP Server - Analysis Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .endpoint {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .log {{ background: #e8f4f8; padding: 5px; margin: 5px 0; font-family: monospace; }}
            </style>
        </head>
        <body>
            <h1>🌈 Color MCP Server</h1>
            <p><strong>Status:</strong> Running (Hybrid Mode)</p>
            <p><strong>MCP Calls Logged:</strong> {len(mcp_log)}</p>
            
            <h2>📡 HTTP Endpoints (para análisis Wireshark):</h2>
            <div class="endpoint">
                <strong>GET /api/hex-to-rgb?hex=FF0000</strong><br>
                Convierte HEX a RGB
            </div>
            <div class="endpoint">
                <strong>GET /api/random-color</strong><br>
                Genera color aleatorio
            </div>
            <div class="endpoint">
                <strong>POST /mcp</strong><br>
                Endpoint JSON-RPC que simula protocolo MCP
            </div>
            
            <h2>📊 <a href="/logs">Ver Logs de MCP</a></h2>
            
            <h3>💡 Para Wireshark:</h3>
            <p>1. Captura tráfico en puerto HTTP<br>
            2. Filtra por: <code>http and tcp.port == {os.environ.get('PORT', '8000')}</code><br>
            3. Analiza requests POST a /mcp para ver JSON-RPC</p>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_logs(self):
        """Send MCP logs"""
        self.send_json_response({
            "mcp_calls": len(mcp_log),
            "logs": mcp_log[-50:],  # Last 50 logs
            "info": "Estos logs muestran las llamadas MCP reales desde tu chatbot"
        })
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

def run_http_server():
    """Run HTTP server in background thread"""
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), AnalysisHandler)
    print(f"🔗 HTTP Analysis Server running on http://0.0.0.0:{port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🔍 Wireshark analysis ready!")
    server.serve_forever()

def main():
    """Main function - Hybrid mode"""
    print("🚀 Starting Hybrid Color MCP Server...")
    print("📡 Mode: MCP (stdio) + HTTP (analysis)")
    
    # Determinar modo según entorno
    if os.environ.get('PORT'):
        # En Render - solo HTTP 
        print("☁️  Cloud mode: HTTP only")
        run_http_server()
    else:
        # Local - MCP stdio + HTTP en thread
        print("💻 Local mode: MCP stdio + HTTP thread")
        
        # Iniciar HTTP server en thread separado
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        
        # Ejecutar MCP server en thread principal
        print("🔧 Starting MCP stdio server...")
        mcp.run()

if __name__ == "__main__":
    main()