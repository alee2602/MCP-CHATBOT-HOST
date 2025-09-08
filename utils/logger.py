import logging
from datetime import datetime
from typing import Dict, List, Any, Optional


class MCPLogger:
    """Sistema de logging especializado para interacciones MCP"""
    
    def __init__(self, log_file: str = "mcp_interactions.log"):
        self.logger = logging.getLogger("MCP_Interactions")
        self.interaction_log: List[Dict[str, Any]] = []
        
        # Configurar logging si no está configurado
        if not self.logger.handlers:
            self._setup_logging(log_file)
    
    def _setup_logging(self, log_file: str):
        """Configurar el sistema de logging"""
        self.logger.setLevel(logging.INFO)
        
        # Formato para los logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para consola (opcional, solo errores)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_tool_call(self, server: str, tool_name: str, params: Dict[str, Any], result: str, success: bool = True, error: Optional[Exception] = None):
        """Registrar llamada a herramienta MCP"""
        timestamp = datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "type": "tool_call",
            "server": server,
            "tool": tool_name,
            "params": params,
            "success": success,
            "result": str(result)[:500] if result else "",  # Limitar para evitar logs enormes
            "error": str(error) if error else None
        }
        
        self.interaction_log.append(interaction)
        
        # Log detallado
        log_msg = f"[{server}] {tool_name}({params}) -> {'SUCCESS' if success else 'ERROR'}"
        if success:
            self.logger.info(log_msg)
        else:
            self.logger.error(f"{log_msg}: {error}")
    
    def log_server_connection(self, server: str, server_type: str, status: str, 
                            tools_count: int = 0, error: Optional[Exception] = None):
        """Registrar conexión a servidor MCP"""
        timestamp = datetime.now().isoformat()
        
        interaction = {
            "timestamp": timestamp,
            "type": "server_connection",
            "server": server,
            "server_type": server_type,
            "status": status,
            "tools_count": tools_count,
            "error": str(error) if error else None
        }
        
        self.interaction_log.append(interaction)
        
        log_msg = f"Server [{server}] ({server_type}): {status}"
        if status == "connected":
            self.logger.info(f"{log_msg} - {tools_count} tools available")
        else:
            self.logger.error(f"{log_msg}: {error}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la sesión actual"""
        total_interactions = len(self.interaction_log)
        tool_calls = [i for i in self.interaction_log if i["type"] == "tool_call"]
        successful_calls = [i for i in tool_calls if i["success"]]
        server_connections = [i for i in self.interaction_log if i["type"] == "server_connection"]
        
        return {
            "total_interactions": total_interactions,
            "tool_calls": {
                "total": len(tool_calls),
                "successful": len(successful_calls),
                "failed": len(tool_calls) - len(successful_calls)
            },
            "servers": {
                "total_connections": len(server_connections),
                "connected": len([s for s in server_connections if s["status"] == "connected"]),
                "failed": len([s for s in server_connections if s["status"] == "failed"])
            }
        }
    
    def print_interaction_log(self, limit: int = 10):
        """Mostrar log de interacciones recientes"""
        print("\n" + "="*60)
        print("📋 MCP INTERACTION LOG")
        print("="*60)
        
        recent_interactions = self.interaction_log[-limit:]
        
        for interaction in recent_interactions:
            timestamp = interaction["timestamp"].split("T")[1].split(".")[0]  # Solo hora
            
            if interaction["type"] == "tool_call":
                status_icon = "✅" if interaction["success"] else "❌"
                print(f"{status_icon} [{timestamp}] {interaction['server']}.{interaction['tool']}")
                print(f"   Params: {interaction['params']}")
                if interaction["success"]:
                    result_preview = interaction["result"][:100] + "..." if len(interaction["result"]) > 100 else interaction["result"]
                    print(f"   Result: {result_preview}")
                else:
                    print(f"   Error: {interaction['error']}")
                print()
            
            elif interaction["type"] == "server_connection":
                status_icon = "🟢" if interaction["status"] == "connected" else "🔴"
                print(f"{status_icon} [{timestamp}] Server: {interaction['server']} ({interaction['server_type']})")
                if interaction["status"] == "connected":
                    print(f"   Tools: {interaction['tools_count']}")
                else:
                    print(f"   Error: {interaction['error']}")
                print()
        
        # Mostrar resumen
        summary = self.get_session_summary()
        print("📊 SESSION SUMMARY:")
        print(f"   Total interactions: {summary['total_interactions']}")
        print(f"   Tool calls: {summary['tool_calls']['successful']}/{summary['tool_calls']['total']} successful")
        print(f"   Servers: {summary['servers']['connected']}/{summary['servers']['total_connections']} connected")
        print("="*60)

    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtener las interacciones más recientes"""
        return self.interaction_log[-limit:]
    
    def clear_log(self):
        """Limpiar el log de interacciones"""
        self.interaction_log.clear()
        self.logger.info("Interaction log cleared")


# Instancia global del logger
mcp_logger = MCPLogger()