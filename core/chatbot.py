import os
import yaml
import requests
import json
from typing import Dict, List, Any, Tuple

from clients.fastmcp import FastMCPClient
from clients.stdio import StdioMCPClient
from clients.http import HTTPMCPClient
#from clients.simple_api import SimpleAPIClient
from utils.logger import mcp_logger
from .config import ANTHROPIC_API_KEY


class ModularMCPChatbot:
    """Chatbot that manages multiple MCP servers"""
    
    def __init__(self, config_file: str = "servers.yaml"):
        self.conversation_history: List[Tuple[str, str]] = []
        self.mcps: Dict[str, Dict[str, Any]] = {}
        self.config_file = config_file
    
    async def load_mcps(self):
        """Load multiple MCPs from configuration"""
        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            
            for name, settings in config.items():
                await self._load_single_mcp(name, settings)
            
            if not self.mcps:
                print("❌ No MCPs connected successfully")
            else:
                print(f"✅ Ready! Connected to {len(self.mcps)} service(s)")
                self._print_servers_summary()
                
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_file} not found")
        except Exception as e:
            print(f"❌ Error loading MCPs: {e}")
    
    async def _load_single_mcp(self, name: str, settings: Dict[str, Any]):
        server_type = settings.get("type", "stdio")
        
        try:
            if server_type == "fastmcp":
                client = await self._create_fastmcp_client(name, settings)
            elif server_type == "stdio":
                client = await self._create_stdio_client(name, settings)
            elif server_type == "http":
                client = await self._create_http_client(name, settings)
            elif server_type == "api":
                client = await self._create_api_client(name, settings)
            else:
                print(f"❌ Unknown server type '{server_type}' for {name}")
                return
            
            tools = await client.initialize()
            anthropic_tools = client.get_anthropic_tools()
            
            self.mcps[name] = {
                "client": client,
                "tools": tools,
                "type": server_type
            }
            
            print(f"🟢 Connected to {name} ({server_type}): {len(tools)} tools, {len(anthropic_tools)} anthropic tools")
            
        except Exception as e:
            print(f"🔴 Failed to connect to {name}: {e}")
    
    async def _create_fastmcp_client(self, name: str, settings: Dict[str, Any]):
        cmd = settings["cmd"]
        cwd = settings.get("cwd", ".")
        server_path = os.path.abspath(os.path.join(cwd, cmd[1]))
        config_module = settings.get("config_module")
        
        return FastMCPClient(server_path, config_module, name)
    
    async def _create_stdio_client(self, name: str, settings: Dict[str, Any]):
        cmd = settings["cmd"]
        cwd = settings.get("cwd", ".")
        config_module = settings.get("config_module")
        
        return StdioMCPClient(cmd, cwd, config_module, name)
    
    async def _create_http_client(self, name: str, settings: Dict[str, Any]):
        url = settings["url"]
        tools = settings.get("tools", [])
        config_module = settings.get("config_module")
        
        return HTTPMCPClient(url, tools, config_module, name)
    
    def _print_servers_summary(self):
        """Show summary of connected servers"""
        print("\n📋 CONNECTED SERVERS:")
        for name, info in self.mcps.items():
            client = info["client"]
            server_info = client.get_server_info()
            print(f"  • {name} ({info['type']}): {server_info['tools_count']} tools")
        print()
    
    async def call_mcp_tool(self, server: str, tool: str, params: Dict[str, Any]) -> str:
        if server not in self.mcps:
            return f"Unknown server: {server}"
        
        client_info = self.mcps[server]
        client = client_info["client"]
        
        try:
            result = await client.call_tool(tool, **params)
            return result
        except Exception as e:
            return f"Error calling {server}:{tool}: {e}"
    
    def get_anthropic_tools(self) -> List[Dict[str, Any]]:
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
    
    async def call_anthropic_with_tools(self, message: str) -> str:
        if not ANTHROPIC_API_KEY:
            return "Please set ANTHROPIC_API_KEY in .env file"
        
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            
            #Use power saving settings
            from .config import DEFAULT_MODEL, MAX_TOKENS, MAX_CONVERSATION_HISTORY, MAX_RESULT_LENGTH
            
            messages = []
            # Limit history according to settings
            for role, content in self.conversation_history[-MAX_CONVERSATION_HISTORY:]:
                messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})
            
            # get tools dynamically
            tools = self.get_anthropic_tools()
            
            # Create mapping of tools to servers
            tool_server_mapping = {}
            clean_tools = []
            
            for tool in tools:
                server = tool.pop('_server', None) 
                tool_server_mapping[tool['name']] = server
                clean_tools.append(tool)
            
            system_message = f"""You are a helpful assistant with access to various tools and services.

Available services: {list(self.mcps.keys())}

Be conversational and natural. Use the appropriate tools when users ask for specific functionality. Keep responses concise."""
            
            payload = {
                "model": DEFAULT_MODEL,  
                "max_tokens": MAX_TOKENS,  
                "system": system_message,
                "messages": messages
            }
            
            # Only add tools if they exist
            if clean_tools:
                payload["tools"] = clean_tools
                payload["tool_choice"] = {"type": "auto"}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                return f"API Error {response.status_code}: {response.text[:200]}"
            
            result = response.json()
            
            # Process response
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
                    
                    # Find the correct server using mapping
                    server = tool_server_mapping.get(tool_name)
                    
                    if server:
                        tool_result = await self.call_mcp_tool(server, tool_name, tool_input)
                        # Truncate tool result to save tokens
                        if len(tool_result) > MAX_RESULT_LENGTH:
                            tool_result = tool_result[:MAX_RESULT_LENGTH] + "..."
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
        print("=" * 40)
        print("Multi-Service Chatbot")
        print("=" * 40)
        
        await self.load_mcps()
        
        print("💬 Chat with me! The assistant will use appropriate tools automatically.")
        print("📝 Commands: '/quit' to exit, '/log' for MCP interactions, '/history' for conversation, '/servers' for server info")
        print()
        
        try:
            while True:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["/quit", "/exit", "/q"]:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == "/log":
                    mcp_logger.print_interaction_log()
                    continue
                elif user_input.lower() == "/servers":
                    self._print_servers_summary()
                    continue
                
                print("🤔 Thinking...")
                response = await self.call_anthropic_with_tools(user_input)
                print(f"\n{response}\n")
                
                self.conversation_history.append(("user", user_input))
                self.conversation_history.append(("assistant", response))
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        # Auto-save conversation if it has messages
        if self.conversation_history:
            self._auto_save_conversation()
        
        # Close MCP Connections
        for info in self.mcps.items():
            try:
                await info["client"].close()
            except:
                pass
    
    def _auto_save_conversation(self):
        try:
            import json
            from datetime import datetime
            import os
            
            filename = "conversation_history.json"
            
            # Read file if it exists
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (json.JSONDecodeError, KeyError):
                    data = {"sessions": []}
            else:
                data = {"sessions": []}
            
            # Add new session only if there are messages
            if self.conversation_history:
                session = {
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.conversation_history
                }
                data["sessions"].append(session)
                
                # Save updated file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"Conversation saved to {filename}")
            
        except Exception as e:
            print(f"Failed to save conversation: {e}")
    
    def _print_conversation_history(self):
        print("\n" + "="*60)
        print("CONVERSATION HISTORY")
        print("="*60)
        
        if not self.conversation_history:
            print("No conversation history yet.")
            return
        
        for i, (role, content) in enumerate(self.conversation_history, 1):
            role_name = "User" if role == "user" else "Assistant"
            
            print(f"\n[{i}] {role_name}:")
            print("-" * 40)
            
            if len(content) > 200:
                print(f"{content[:200]}...")
                print(f"[Message truncated - {len(content)} total characters]")
            else:
                print(content)
        
        print(f"\nTotal messages: {len(self.conversation_history)}")
        user_count = len([h for h in self.conversation_history if h[0] == "user"])
        assistant_count = len([h for h in self.conversation_history if h[0] == "assistant"])
        print(f"User messages: {user_count}")
        print(f"Assistant messages: {assistant_count}")
        print("="*60)
    
    def get_conversation_history(self) -> List[Tuple[str, str]]:
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        self.conversation_history.clear()
    
    def get_server_status(self) -> Dict[str, Any]:
        status = {}
        for name, info in self.mcps.items():
            client = info["client"]
            status[name] = client.get_server_info()
        return status