import requests
import importlib.util
from typing import List, Dict, Any, Optional

from .base import BaseMCPClient
from utils.logger import mcp_logger


class SimpleAPIClient(BaseMCPClient):
    """Cliente para APIs simples (no MCP)"""
    
    def __init__(self, base_url: str, endpoints: Dict[str, str], config_module: Optional[str] = None, server_name: str = "api"):
        super().__init__(server_name)
        self.base_url = base_url
        self.endpoints = endpoints
        self._tools = list(endpoints.keys())
        self.config_module = config_module
        
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
    
    async def initialize(self) -> List[str]:
        """Inicializar API simple"""
        try:
            # Log successful connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "api", 
                "connected", 
                len(self._tools)
            )
        except Exception as e:
            # Log failed connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "api", 
                "failed", 
                error=e
            )
            
        return self._tools
    
    async def call_tool(self, tool_name: str, **params) -> str:
        """Llamar API simple"""
        try:
            if tool_name not in self.endpoints:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            endpoint = self.endpoints[tool_name]
            url = f"{self.base_url}{endpoint}"
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result_str = response.text
            
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
    
    async def list_tools(self) -> List[str]:
        return self._tools