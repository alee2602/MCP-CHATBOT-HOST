import requests
import importlib.util
from typing import List, Dict, Any, Optional

from .base import BaseMCPClient
from utils.logger import mcp_logger

class HTTPMCPClient(BaseMCPClient):
    """Client for MCPs over HTTP"""
    
    def __init__(self, url: str, tools: Optional[List[str]] = None, config_module: Optional[str] = None, server_name: str = "http"):
        super().__init__(server_name)
        self.url = url
        self._id = 0
        self._tools = tools or []
        self.config_module = config_module
        
        if self.config_module:
            self._load_tool_config()
    
    def _load_tool_config(self):
        """Load specific tool settings"""
        try:
            spec = importlib.util.spec_from_file_location("tool_config", self.config_module)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            if hasattr(config_module, 'ANTHROPIC_TOOLS'):
                self.anthropic_tools = config_module.ANTHROPIC_TOOLS
        except Exception as e:
            print(f"Warning: Could not load tool config: {e}")
    
    async def initialize(self) -> List[str]:
        """Initialize and obtain available tools"""
        try:
            result = await self.call("tools/list")
            if isinstance(result, dict) and "tools" in result:
                self._tools = [tool["name"] for tool in result["tools"]]
            
            # Log successful connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "http", 
                "connected", 
                len(self._tools)
            )
            
        except Exception as e:
            # Log failed connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "http", 
                "failed", 
                error=e
            )
            # Keep predefined tools
            pass
        
        return self._tools
    
    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP JSON-RPC call"""
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
    
    async def call_tool(self, tool_name: str, **params) -> str:
        """Call tool via HTTP"""
        try:
            result = await self.call("tools/call", {"name": tool_name, "arguments": params})
            
            result_str = self._process_result(result)
            
            # Log successful call
            mcp_logger.log_tool_call(
                self.server_name, 
                tool_name, 
                params, 
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
        """Process HTTP tool result"""
        if isinstance(result, dict) and "content" in result:
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", str(result))
        
        return str(result)
    
    async def list_tools(self) -> List[str]:
        return self._tools