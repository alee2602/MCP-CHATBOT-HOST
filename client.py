import subprocess
import json
import threading
import queue
import time
import yaml
import os

class MCPClient:
    def __init__(self, cmd, cwd=None):
        self.cmd = cmd
        self.cwd = cwd
        self.process = None
        self.response_queue = queue.Queue()
        self._id = 0
        self._initialized = False
        self.start_process()
    
    def start_process(self):
        """Inicia el proceso MCP"""
        print(f"Starting MCP: {' '.join(self.cmd)} in {self.cwd}")
        
        try:
            self.process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Iniciar thread para leer stdout
            threading.Thread(target=self._read_stdout, daemon=True).start()
            
            # Dar tiempo al proceso para arrancar
            time.sleep(1)
            
            # Verificar que el proceso sigue vivo
            if self.process.poll() is not None:
                stderr_output = self.process.stderr.read()
                raise RuntimeError(f"Process died immediately. STDERR: {stderr_output}")
                
            print(f"Process started successfully (PID: {self.process.pid})")
            
        except Exception as e:
            print(f"Failed to start process: {e}")
            raise
    
    def _read_stdout(self):
        """Lee respuestas del proceso MCP"""
        buffer = ""
        
        while self.process and self.process.poll() is None:
            try:
                char = self.process.stdout.read(1)
                if not char:
                    break
                    
                buffer += char
                
                # Buscar mensaje completo
                if "Content-Length:" in buffer and "\r\n\r\n" in buffer:
                    try:
                        # Extraer Content-Length
                        header_end = buffer.find("\r\n\r\n")
                        header = buffer[:header_end]
                        
                        content_length = 0
                        for line in header.split("\r\n"):
                            if line.startswith("Content-Length:"):
                                content_length = int(line.split(":")[1].strip())
                                break
                        
                        # Leer el cuerpo del mensaje
                        body_start = header_end + 4
                        while len(buffer) < body_start + content_length:
                            char = self.process.stdout.read(1)
                            if not char:
                                break
                            buffer += char
                        
                        # Extraer y parsear el mensaje JSON
                        message_body = buffer[body_start:body_start + content_length]
                        
                        try:
                            response = json.loads(message_body)
                            self.response_queue.put(response)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            print(f"Message body: {message_body}")
                        
                        # Limpiar buffer
                        buffer = buffer[body_start + content_length:]
                        
                    except Exception as e:
                        print(f"Protocol error: {e}")
                        buffer = ""
                        
            except Exception as e:
                print(f"Read error: {e}")
                break
    
    def _send_message(self, message):
        """Envía mensaje al proceso MCP"""
        json_str = json.dumps(message)
        content = f"Content-Length: {len(json_str)}\r\n\r\n{json_str}"
        
        try:
            self.process.stdin.write(content)
            self.process.stdin.flush()
        except Exception as e:
            print(f"Send error: {e}")
            raise
    
    def _wait_for_response(self, request_id, timeout=10):
        """Espera respuesta específica"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.response_queue.get(timeout=1)
                if response.get("id") == request_id:
                    return response
                else:
                    # Reencolar si es diferente ID
                    self.response_queue.put(response)
            except queue.Empty:
                continue
                
        raise RuntimeError(f"Timeout waiting for response {request_id}")
    
    def initialize(self):
        """Inicializar conexión MCP"""
        if self._initialized:
            return True
        
        self._id += 1
        init_message = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "simple-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize...")
        self._send_message(init_message)
        
        try:
            response = self._wait_for_response(self._id)
            if "error" in response:
                print(f"Initialize error: {response['error']}")
                return False
            else:
                print("Initialize successful!")
                self._initialized = True
                return True
        except Exception as e:
            print(f"Initialize failed: {e}")
            return False
    
    def call(self, method, params=None):
        """Llamar método MCP"""
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize")
        
        self._id += 1
        message = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params or {}
        }
        
        self._send_message(message)
        
        try:
            response = self._wait_for_response(self._id)
            if "error" in response:
                raise RuntimeError(f"Method error: {response['error']}")
            return response.get("result")
        except Exception as e:
            print(f"Call failed: {e}")
            raise
    
    def close(self):
        """Cerrar conexión"""
        if self.process:
            self.process.terminate()
            self.process.wait()

def load_clients(config_file="servers.yaml"):
    """Cargar clientes desde configuración"""
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    clients = {}
    for name, settings in config.items():
        if settings.get("type") == "stdio":
            cmd = settings["cmd"]
            cwd = settings.get("cwd", ".")
            clients[name] = MCPClient(cmd, cwd)
    
    return clients