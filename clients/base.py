from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseMCPClient(ABC):
    """Clase base abstracta para todos los tipos de clientes MCP"""
    
    def __init__(self, server_name: str = "unknown"):
        self.server_name = server_name
        self._tools: List[str] = []
        self.anthropic_tools: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def initialize(self) -> List[str]:
        """
        Inicializar el cliente y obtener lista de herramientas disponibles
        Returns: Lista de nombres de herramientas
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, **params) -> str:
        """
        Llamar una herramienta específica
        Args:
            tool_name: Nombre de la herramienta
            **params: Parámetros para la herramienta
        Returns: Resultado de la herramienta como string
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[str]:
        """
        Obtener lista de herramientas disponibles
        Returns: Lista de nombres de herramientas
        """
        pass
    
    async def close(self):
        """Cerrar conexiones y limpiar recursos (opcional)"""
        pass
    
    def get_anthropic_tools(self) -> List[Dict[str, Any]]:
        """
        Obtener definiciones de herramientas para Anthropic API
        Returns: Lista de definiciones de herramientas
        """
        return self.anthropic_tools
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Obtener información básica del servidor
        Returns: Diccionario con información del servidor
        """
        return {
            "name": self.server_name,
            "tools_count": len(self._tools),
            "tools": self._tools,
            "anthropic_tools_count": len(self.anthropic_tools)
        }