from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMCPClient(ABC):
    """Abstract base class for all types of MCP clients"""
    
    def __init__(self, server_name: str = "unknown"):
        self.server_name = server_name
        self._tools: List[str] = []
        self.anthropic_tools: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def initialize(self) -> List[str]:
        """
        Initialize the client and obtain a list of available tools
        Returns: List of tool names
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, **params) -> str:
        """
        Call a specific tool
        Args:
            tool_name: Name of the tool
            **params: Parameters for the tool
        Returns: Result of the tool as a string
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[str]:
        """
        Get list of available tools
        Returns: List of tool names
        """
        pass
    
    async def close(self):
        """Close connections and clean up resources"""
        pass
    
    def get_anthropic_tools(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for Anthropic API
        Returns: List of tool definitions
        """
        return self.anthropic_tools
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get basic server information
        Returns: Dictionary with server information
        """
        return {
            "name": self.server_name,
            "tools_count": len(self._tools),
            "tools": self._tools,
            "anthropic_tools_count": len(self.anthropic_tools)
        }