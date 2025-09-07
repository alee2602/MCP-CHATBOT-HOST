import asyncio
import os
import yaml
import requests
import json
import importlib.util
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class BaseMCPClient:
    """Clase base para todos los tipos de clientes MCP"""
    async def call_tool(self, tool_name, **params):
        raise NotImplementedError
    
    async def list_tools(self):
        raise NotImplementedError
    
    async def close(self):
        pass

class FastMCPClient(BaseMCPClient):
    """Cliente para FastMCP - carga configuración desde archivo externo"""
    def __init__(self, server_path, config_module=None):
        self.server_path = server_path
        self.config_module = config_module
        self._tools = []
        self.tool_configs = {}
        self.anthropic_tools = []
    
    async def initialize(self):
        """Inicializar y cargar configuración de herramientas"""
        if self.config_module:
            self._load_tool_config()
        
        client = Client(self.server_path)
        async with client:
            await client.ping()
            tools = await client.list_tools()
            
            if hasattr(tools, 'tools'):
                self._tools = [tool.name for tool in tools.tools]
            elif isinstance(tools, list):
                self._tools = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
            else:
                self._tools = []
        
        return self._tools
    
    async def call_tool(self, tool_name, **params):
        """
        Call a FastMCP tool passing arguments as a single dict (not kwargs).
        Uses optional param mapping from self.tool_configs[tool_name].
        Returns a string-friendly result.
        """
        # Clean & map params
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        if getattr(self, "tool_configs", None) and tool_name in self.tool_configs:
            mapping = self.tool_configs[tool_name] or {}
            args_dict = {mapping.get(k, k): v for k, v in clean_params.items()}
        else:
            args_dict = clean_params

        #print(f"Debug - Calling {tool_name} with params: {args_dict}")

        # Call the tool (dict as one argument)
        client = Client(self.server_path)  # self.server_path: path to your server script
        async with client:
            try:
                result = await client.call_tool(tool_name, arguments=args_dict)
            except TypeError:
                # Fallback for older signatures: pass the dict positionally
                result = await client.call_tool(tool_name, args_dict)

        # Normalize result
        if result is None:
            return ""

        # ToolResponse-style: prefer textual blocks
        content = getattr(result, "content", None)
        if content:
            parts = []
            for block in content:
                # block may be an object with .text or a dict with "text"
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
                elif isinstance(block, dict) and "text" in block:
                    parts.append(block["text"])
                else:
                    try:
                        parts.append(json.dumps(block, ensure_ascii=False))
                    except Exception:
                        parts.append(str(block))
            if parts:
                return "\n".join(parts)

        # Some clients expose .data
        if hasattr(result, "data"):
            try:
                return json.dumps(result.data, ensure_ascii=False)
            except Exception:
                return str(result.data)

        # Strings / bytes / other
        if isinstance(result, bytes):
            return result.decode("utf-8", errors="ignore")
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result, ensure_ascii=False)
        except Exception:
            return str(result)

    
    async def list_tools(self):
        return self._tools
    
    def get_anthropic_tools(self):
        """Obtener definiciones de herramientas para Anthropic API"""
        return self.anthropic_tools
    
    def _load_tool_config(self):
        """
        Load tool config from a Python module.

        - self.config_module puede ser una ruta a archivo (p.ej. "mymcpserver/music_tools.py")
        o un módulo con dotted path (p.ej. "mymcpserver.music_tools").
        - Rellena:
            self.tool_configs  <- module.TOOL_CONFIGS (dict) o {}
            self.anthropic_tools <- module.ANTHROPIC_TOOLS (list) o []
        """
        import os, sys, importlib, importlib.util

        if not self.config_module:
            return

        ref = self.config_module.replace("\\", "/").strip()

        if ref.endswith(".py") or "/" in ref:
            path = os.path.abspath(ref)
            if not os.path.exists(path):
                cand = os.path.abspath(os.path.join(os.getcwd(), ref))
                if os.path.exists(cand):
                    path = cand
                else:
                    here = os.path.dirname(os.path.abspath(__file__))
                    cand2 = os.path.abspath(os.path.join(here, ref))
                    if os.path.exists(cand2):
                        path = cand2
                    else:
                        raise FileNotFoundError(f"Tool config file not found: {self.config_module}")

            spec = importlib.util.spec_from_file_location("tool_config_module", path)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
        else:
            mod = importlib.import_module(ref)

        self.tool_configs = getattr(mod, "TOOL_CONFIGS", {}) or {}
        self.anthropic_tools = getattr(mod, "ANTHROPIC_TOOLS", []) or []

class HTTPMCPClient(BaseMCPClient):
    """Cliente para MCPs sobre HTTP"""
    def __init__(self, url, tools=None, config_module=None):
        self.url = url
        self._id = 0
        self._tools = tools or []
        self.config_module = config_module
        self.anthropic_tools = []
        
        if self.config_module:
            self._load_tool_config()
    
    def _load_tool_config(self):
        """Cargar configuración específica de herramientas"""
        try:
            spec = importlib.util.spec_from_file_location("tool_config", self.config_module)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            if hasattr(config_module, 'ANTHROPIC_TOOLS'):
                self.anthropic_tools = config_module.ANTHROPIC_TOOLS
        except Exception as e:
            print(f"Warning: Could not load tool config: {e}")
    
    async def initialize(self):
        """Inicializar y obtener herramientas disponibles"""
        try:
            result = await self.call("tools/list")
            if isinstance(result, dict) and "tools" in result:
                self._tools = [tool["name"] for tool in result["tools"]]
        except:
            pass  # Keep predefined tools
        return self._tools
    
    async def call(self, method, params=None):
        """Llamada HTTP JSON-RPC"""
        self._id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(self.url, json=request, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise RuntimeError(result["error"])
        return result.get("result")
    
    async def call_tool(self, tool_name, **params):
        """Llamar herramienta via HTTP"""
        result = await self.call("tools/call", {"name": tool_name, "arguments": params})
        
        if isinstance(result, dict) and "content" in result:
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", str(result))
        
        return str(result)
    
    async def list_tools(self):
        return self._tools
    
    def get_anthropic_tools(self):
        """Obtener definiciones de herramientas para Anthropic API"""
        return self.anthropic_tools

class SimpleAPIClient(BaseMCPClient):
    """Cliente para APIs simples (no MCP)"""
    def __init__(self, base_url, endpoints, config_module=None):
        self.base_url = base_url
        self.endpoints = endpoints
        self._tools = list(endpoints.keys())
        self.config_module = config_module
        self.anthropic_tools = []
        
        if self.config_module:
            self._load_tool_config()
    
    def _load_tool_config(self):
        """Cargar configuración específica de herramientas"""
        try:
            spec = importlib.util.spec_from_file_location("tool_config", self.config_module)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            if hasattr(config_module, 'ANTHROPIC_TOOLS'):
                self.anthropic_tools = config_module.ANTHROPIC_TOOLS
        except Exception as e:
            print(f"Warning: Could not load tool config: {e}")
    
    async def initialize(self):
        return self._tools
    
    async def call_tool(self, tool_name, **params):
        """Llamar API simple"""
        if tool_name not in self.endpoints:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        endpoint = self.endpoints[tool_name]
        url = f"{self.base_url}{endpoint}"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.text
    
    async def list_tools(self):
        return self._tools
    
    def get_anthropic_tools(self):
        """Obtener definiciones de herramientas para Anthropic API"""
        return self.anthropic_tools

class ModularMCPChatbot:
    def __init__(self, config_file="servers.yaml"):
        self.conversation_history = []
        self.mcps = {}
        self.config_file = config_file
    
    async def load_mcps(self):
        """Cargar múltiples MCPs desde configuración"""
        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            
            for name, settings in config.items():
                server_type = settings.get("type", "stdio")
                
                try:
                    if server_type == "fastmcp":
                        cmd = settings["cmd"]
                        cwd = settings.get("cwd", ".")
                        server_path = os.path.abspath(os.path.join(cwd, cmd[1]))
                        config_module = settings.get("config_module")
                        
                        #print(f"Debug - Configurando FastMCP:")
                        #print(f"  - server_path: {server_path}")
                        #print(f"  - config_module: {config_module}")
                        
                        client = FastMCPClient(server_path, config_module)
                        tools = await client.initialize()
                        
                        # Debug adicional
                        anthropic_tools = client.get_anthropic_tools()
                        #print(f"  - tools encontradas: {tools}")
                        #print(f"  - anthropic_tools: {len(anthropic_tools)}")
                        
                        self.mcps[name] = {
                            "client": client,
                            "tools": tools,
                            "type": server_type
                        }
                        
                        print(f"Connected to {name} FastMCP ({len(tools)} tools, {len(anthropic_tools)} anthropic tools)")
                        
                    elif server_type == "http":
                        config_module = settings.get("config_module")
                        client = HTTPMCPClient(settings["url"], settings.get("tools", []), config_module)
                        tools = await client.initialize()
                        
                        self.mcps[name] = {
                            "client": client,
                            "tools": tools,
                            "type": server_type
                        }
                        
                        print(f"Connected to {name} HTTP MCP ({len(tools)} tools)")
                    
                    elif server_type == "api":
                        config_module = settings.get("config_module")
                        client = SimpleAPIClient(settings["base_url"], settings["endpoints"], config_module)
                        tools = await client.initialize()
                        
                        self.mcps[name] = {
                            "client": client,
                            "tools": tools,
                            "type": server_type
                        }
                        
                        print(f"Connected to {name} Simple API ({len(tools)} endpoints)")
                        
                except Exception as e:
                    print(f"Failed to connect to {name}: {e}")
            
            if not self.mcps:
                print("No MCPs connected successfully")
            else:
                print(f"Ready! Connected to {len(self.mcps)} service(s)")
                
        except FileNotFoundError:
            print(f"Configuration file {self.config_file} not found")
        except Exception as e:
            print(f"Error loading MCPs: {e}")
    
    async def call_mcp_tool(self, server, tool, params):
        """Llamar herramienta de cualquier tipo de servidor"""
        if server not in self.mcps:
            return f"Unknown server: {server}"
        
        client_info = self.mcps[server]
        client = client_info["client"]
        
        try:
            result = await client.call_tool(tool, **params)
            return result
        except Exception as e:
            return f"Error calling {server}:{tool}: {e}"
    
    def get_anthropic_tools(self):
        """Obtener todas las herramientas para Anthropic API dinámicamente"""
        tools = []
        
        for server, info in self.mcps.items():
            client = info["client"]
            if hasattr(client, 'get_anthropic_tools'):
                server_tools = client.get_anthropic_tools()
                for tool in server_tools:
                    clean_tool = {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["input_schema"]
                    }
                    clean_tool["_server"] = server
                    tools.append(clean_tool)
        
        return tools
    
    async def call_anthropic_with_tools(self, message):
        """Call Anthropic API with dynamic tool calling"""
        if not ANTHROPIC_API_KEY:
            return "Please set ANTHROPIC_API_KEY in .env file"
        
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            
            messages = []
            for role, content in self.conversation_history[-5:]:
                messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})
            
            # Obtener herramientas dinámicamente
            tools = self.get_anthropic_tools()
            
            # Crear mapping de herramientas a servidores
            tool_server_mapping = {}
            clean_tools = []
            
            for tool in tools:
                server = tool.pop('_server', None) 
                tool_server_mapping[tool['name']] = server
                clean_tools.append(tool)
            
            system_message = f"""You are a helpful assistant with access to various tools and services.

Available services: {list(self.mcps.keys())}

Be conversational and natural. Use the appropriate tools when users ask for specific functionality."""
            
            # Construir payload básico
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 120,
                "system": system_message,
                "messages": messages
            }
            
            # Solo añadir tools si existen
            if clean_tools:
                payload["tools"] = clean_tools
                payload["tool_choice"] = {"type": "auto"}
            
            #print(f"Debug - Enviando {len(clean_tools)} herramientas limpias")  # Debug
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Debug para ver la respuesta de error
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return f"API Error {response.status_code}: {response.text[:200]}"
            
            result = response.json()
            
            # Procesar respuesta
            response_text = ""
            tool_results = []
            
            if "content" not in result:
                return f"Unexpected response format: {result}"
            
            for content in result["content"]:
                if content["type"] == "text":
                    response_text += content["text"]
                elif content["type"] == "tool_use":
                    tool_name = content["name"]
                    tool_input = content["input"]
                    
                    # Buscar el servidor correcto usando el mapping
                    server = tool_server_mapping.get(tool_name)
                    
                    if server:
                        tool_result = await self.call_mcp_tool(server, tool_name, tool_input)
                        tool_results.append(f"Tool result: {tool_result}")
                    else:
                        tool_results.append(f"Tool {tool_name} not found in any server")
            
            if tool_results:
                if response_text:
                    response_text += "\n\n"
                response_text += "\n\n".join(tool_results)
            
            return response_text if response_text else "I couldn't process that request."
            
        except requests.exceptions.RequestException as e:
            return f"Network error: {e}"
        except json.JSONDecodeError as e:
            return f"JSON decode error: {e}"
        except Exception as e:
            return f"Error calling Anthropic: {e}"
    
    async def chat(self):
        """Main chat loop"""
        print("Modular Multi-Service Chatbot")
        print("="*35)
        
        await self.load_mcps()
        
        print("\nYou can chat naturally! The assistant will use appropriate tools automatically.")
        print("Type '/quit' to exit.\n")
        
        try:
            while True:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["/quit", "/exit", "/q"]:
                    print("Goodbye!")
                    break
                
                print("Thinking...")
                response = await self.call_anthropic_with_tools(user_input)
                print(f"\n{response}\n")
                
                self.conversation_history.append(("user", user_input))
                self.conversation_history.append(("assistant", response))
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
        
        finally:
            for name, info in self.mcps.items():
                try:
                    await info["client"].close()
                except:
                    pass

async def main():
    chatbot = ModularMCPChatbot()
    await chatbot.chat()

if __name__ == "__main__":
    asyncio.run(main())