import os
import sys
import json
import importlib
import importlib.util
from typing import List, Dict, Any, Optional

from fastmcp import Client
from .base import BaseMCPClient
from utils.logger import mcp_logger

class FastMCPClient(BaseMCPClient):
    """Cliente para FastMCP - carga configuración desde archivo externo"""
    
    def __init__(self, server_path: str, config_module: Optional[str] = None, server_name: str = "fastmcp"):
        super().__init__(server_name)
        self.server_path = server_path
        self.config_module = config_module
        self.tool_configs: Dict[str, Dict[str, str]] = {}
    
    async def initialize(self) -> List[str]:
        """Inicializar y cargar configuración de herramientas"""
        try:
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
            
            # Log successful connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "fastmcp", 
                "connected", 
                len(self._tools)
            )
            
            return self._tools
            
        except Exception as e:
            # Log failed connection
            mcp_logger.log_server_connection(
                self.server_name, 
                "fastmcp", 
                "failed", 
                error=e
            )
            raise
    
    async def call_tool(self, tool_name: str, **params) -> str:
        """
        Call a FastMCP tool passing arguments as a single dict.
        Uses optional param mapping from self.tool_configs[tool_name].
        Returns a string-friendly result.
        """
        try:
            # Clean & map params
            clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
            if self.tool_configs and tool_name in self.tool_configs:
                mapping = self.tool_configs[tool_name] or {}
                args_dict = {mapping.get(k, k): v for k, v in clean_params.items()}
            else:
                args_dict = clean_params

            # Call the tool
            client = Client(self.server_path)
            async with client:
                try:
                    result = await client.call_tool(tool_name, arguments=args_dict)
                except TypeError:
                    # Fallback for older signatures
                    result = await client.call_tool(tool_name, args_dict)

            # Normalize result
            result_str = self._normalize_result(result)
            
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
    
    def _normalize_result(self, result) -> str:
        """Normalizar el resultado de una herramienta a string"""
        if result is None:
            return ""

        # ToolResponse-style: prefer textual blocks
        content = getattr(result, "content", None)
        if content:
            parts = []
            for block in content:
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
    
    async def list_tools(self) -> List[str]:
        return self._tools
    
    def _load_tool_config(self):
        """
        Load tool config from a Python module.
        
        Fills:
            self.tool_configs  <- module.TOOL_CONFIGS (dict) or {}
            self.anthropic_tools <- module.ANTHROPIC_TOOLS (list) or []
        """
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
            
        except Exception as e:
            print(f"Warning: Could not load tool config from {self.config_module}: {e}")