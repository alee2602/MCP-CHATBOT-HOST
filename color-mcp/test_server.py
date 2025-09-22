#!/usr/bin/env python3

import sys
import os
import time

print("=== DEBUG START ===")
print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")
print(f"Files in current dir: {os.listdir('.')}")

try:
    print("Testing fastmcp import...")
    from fastmcp import FastMCP
    print("✅ fastmcp import SUCCESS")
    
    print("Creating server...")
    mcp = FastMCP("DebugServer")
    print("✅ Server created SUCCESS")
    
    @mcp.tool()
    def debug_tool() -> str:
        return "Debug working!"
    
    print("✅ Tool registered SUCCESS")
    print("Starting server...")
    
    # Intentar iniciar servidor
    mcp.run()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Mantener proceso vivo
print("Keeping alive...")
while True:
    time.sleep(30)
    print("Still running...")