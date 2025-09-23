"""
Cliente para servidores MCP oficiales que usan stdio
"""

import asyncio
import json
import os
import sys
import importlib.util
from typing import List, Dict, Any, Optional

from .base import BaseMCPClient
from utils.logger import mcp_logger


class StdioMCPClient(BaseMCPClient):
    """Client for official MCP servers using stdio"""
    
    def __init__(self, cmd: List[str], cwd: str = ".", config_module: Optional[str] = None, server_name: str = "stdio"):
        super().__init__(server_name)
        self.cmd = cmd
        self.cwd = cwd
        self.config_module = config_module
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tool_configs: Dict[str, Dict[str, str]] = {}
        self._next_id = 1
    
    async def initialize(self) -> List[str]:
        """Initialize process and obtain tools"""
        try:
            if self.config_module:
                self._load_tool_config()
            
            self.process = await asyncio.create_subprocess_exec(
                *self.cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            
            # Initialize connection
            await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "modular-chatbot",
                    "version": "1.0.0"
                }
            })
            
            # Get list of tools
            tools_response = await self._send_request("tools/list", {})
            if tools_response and "tools" in tools_response:
                self._tools = [tool["name"] for tool in tools_response["tools"]]
            
            # Log successful connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "stdio", 
                "connected", 
                len(self._tools)
            )
            
            return self._tools
            
        except Exception as e:
            # Log failed connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "stdio", 
                "failed", 
                error=e
            )
            raise
    
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to the server"""
        if not self.process:
            raise RuntimeError("Process not initialized")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id,
            "method": method,
            "params": params or {}
        }
        self._next_id += 1
        
        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()
        
        # Read response
        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), 
                timeout=10.0
            )
            if not response_line:
                raise RuntimeError("No response from server")
            
            response = json.loads(response_line.decode().strip())
            
            if "error" in response:
                raise RuntimeError(f"Server error: {response['error']}")
            
            return response.get("result")
            
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout waiting for server response")
    
    async def call_tool(self, tool_name: str, **params) -> str:
        """Call MCP server tool"""
        try:
            clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
            if self.tool_configs and tool_name in self.tool_configs:
                mapping = self.tool_configs[tool_name] or {}
                args_dict = {mapping.get(k, k): v for k, v in clean_params.items()}
            else:
                args_dict = clean_params
            
            result = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": args_dict
            })
            
            # Procesar response
            result_str = self._process_result(result)
            
            # Log successful call
            mcp_logger.log_tool_call(
                self.server_name, 
                tool_name, 
                args_dict, 
                result_str, 
                success=True
            )
            
            return result_str
            
        except Exception as e:
            # Log failed call
            mcp_logger.log_tool_call(
                self.server_name, 
                tool_name, 
                params, 
                "", 
                success=False, 
                error=e
            )
            raise
    
    def _process_result(self, result) -> str:
        """Process MCP server result"""
        if not result:
            return ""
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and content:
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if "text" in block:
                            parts.append(block["text"])
                        elif "data" in block:
                            parts.append(str(block["data"]))
                        else:
                            parts.append(json.dumps(block, ensure_ascii=False))
                    else:
                        parts.append(str(block))
                return "\n".join(parts) if parts else ""
        
        return str(result)
    
    async def list_tools(self) -> List[str]:
        return self._tools
    
    def _load_tool_config(self):
        """Load tool settings from Python module"""
        if not self.config_module:
            return
        
        try:
            ref = self.config_module.replace("\\", "/").strip()
            
            if ref.endswith(".py") or "/" in ref:
                path = os.path.abspath(ref)
                if not os.path.exists(path):
                    candidates = [
                        os.path.abspath(os.path.join(os.getcwd(), ref)),
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ref))
                    ]
                    for cand in candidates:
                        if os.path.exists(cand):
                            path = cand
                            break
                    else:
                        print(f"Warning: Tool config file not found: {self.config_module}")
                        return
                
                spec = importlib.util.spec_from_file_location("tool_config_module", path)
                if not spec or not spec.loader:
                    print(f"Warning: Could not load spec for {path}")
                    return
                
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
            else:
                mod = importlib.import_module(ref)
            
            self.tool_configs = getattr(mod, "TOOL_CONFIGS", {}) or {}
            self.anthropic_tools = getattr(mod, "ANTHROPIC_TOOLS", []) or []
            
        except Exception as e:
            print(f"Warning: Could not load tool config from {self.config_module}: {e}")
    
    async def close(self):
        """Cerrar el proceso del servidor"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except:
                if self.process.returncode is None:
                    self.process.kill()
                    await self.process.wait()