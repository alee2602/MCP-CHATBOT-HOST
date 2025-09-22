print("Servidor iniciando...")
from fastmcp import FastMCP
print("FastMCP importado correctamente")

from mcp.server.fastmcp import FastMCP
print("FastMCP clase importada")

mcp = FastMCP("TestServer")
print("Servidor creado")

@mcp.tool()
def test_tool() -> str:
    return "Test funcionando"

print("Tool registrado")

if __name__ == "__main__":
    print("Ejecutando servidor...")
    mcp.run()