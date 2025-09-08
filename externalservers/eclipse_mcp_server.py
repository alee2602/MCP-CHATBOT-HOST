#!/usr/bin/env python3
"""
Servidor MCP personalizado para cálculo de eclipses (versión con base de datos interna)
"""

import asyncio
import json
import sys
from datetime import datetime

# Importaciones MCP
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# --- Base de Datos de Eclipses Ampliada ---
ECLIPSES_DATA = {
    "2025-03-14": {
        "type": "lunar_total", "description": "Total Lunar Eclipse",
        "locations": {
            "Guatemala City": {"visible": True, "partial": False, "coverage": "100%", "max_time": "04:58:00"},
            "Madrid": {"visible": True, "partial": True, "coverage": "60%", "max_time": "06:30:00"},
        }
    },
    "2025-09-07": {
        "type": "lunar_total", "description": "Total Lunar Eclipse",
        "locations": {
            "Sydney": {"visible": True, "partial": False, "coverage": "100%", "max_time": "21:00:00"},
            "Guatemala City": {"visible": False, "partial": False, "coverage": "0%"},
        }
    },
    "2026-02-17": {
        "type": "solar_annular", "description": "Annular Solar Eclipse",
        "locations": {"Guatemala City": {"visible": True, "partial": True, "coverage": "35%", "max_time": "13:30:00"}},
    },
    "2026-08-12": {
        "type": "solar_total", "description": "Total Solar Eclipse",
        "locations": {"Madrid": {"visible": True, "partial": False, "coverage": "100%", "max_time": "19:30:00"}},
    },
    "2028-01-11": {
        "type": "lunar_total", "description": "Total Lunar Eclipse",
        "locations": {"Guatemala City": {"visible": True, "partial": False, "coverage": "100%", "max_time": "22:15:00"}},
    },
    "2028-07-22": {
        "type": "solar_total", "description": "Total Solar Eclipse",
        "locations": {"Sydney": {"visible": True, "partial": False, "coverage": "100%", "max_time": "14:15:00"}},
    },
    "2030-06-01": {
        "type": "solar_annular", "description": "Annular Solar Eclipse",
        "locations": {"Guatemala City": {"visible": True, "partial": True, "coverage": "45%", "max_time": "12:45:00"}},
    },
}

class EclipseCalculatorServer:
    def __init__(self):
        self.server = Server("eclipse-calculator-db")

    async def list_eclipses_by_year(self, year: int) -> dict:
        eclipses_in_year = []
        for date, data in ECLIPSES_DATA.items():
            if date.startswith(str(year)):
                visible_locations = [loc for loc, loc_data in data.get("locations", {}).items() if loc_data.get("visible")]
                eclipses_in_year.append({
                    "date": date, 
                    "type": data.get("type"), 
                    "description": data.get("description", "N/A"),
                    "visible_in": visible_locations
                })
        return {"year": year, "eclipses": eclipses_in_year}

    async def calculate_eclipse_visibility(self, date: str, location: str) -> dict:
        eclipse_data = ECLIPSES_DATA.get(date)
        if not eclipse_data:
            return {"error": "No eclipse data available for this date"}
        location_data = eclipse_data["locations"].get(location)
        if not location_data:
            return {"error": f"Location '{location}' not in database for this eclipse"}
        return {"date": date, "location": location, "eclipse_type": eclipse_data["type"], **location_data}

    async def predict_next_eclipse(self, location: str, after_date: str = None) -> dict:
        if not after_date:
            after_date = datetime.now().strftime("%Y-%m-%d")
        future_eclipses = []
        for date, eclipse_data in ECLIPSES_DATA.items():
            if date > after_date:
                if location in eclipse_data["locations"] and eclipse_data["locations"][location].get("visible"):
                    future_eclipses.append({
                        "date": date,
                        "type": eclipse_data.get("type"),
                        "description": eclipse_data.get("description", "N/A"),
                        "coverage": eclipse_data["locations"][location].get("coverage")
                    })
        if not future_eclipses:
            return {"error": "No upcoming eclipses found in database for this location"}
        future_eclipses.sort(key=lambda x: x["date"])
        return {"location": location, "next_eclipse": future_eclipses[0]}

    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="list_eclipses_by_year",
                    description="List all known eclipses for a given year",
                    inputSchema={
                        "type": "object",
                        "properties": {"year": {"type": "integer"}},
                        "required": ["year"]
                    }
                ),
                types.Tool(
                    name="calculate_eclipse_visibility",
                    description="Calculate eclipse visibility for a date and location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "location": {"type": "string"}
                        },
                        "required": ["date", "location"]
                    }
                ),
                types.Tool(
                    name="predict_next_eclipse",
                    description="Predict next visible eclipse for a location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "after_date": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            if name == "list_eclipses_by_year":
                result = await self.list_eclipses_by_year(arguments.get("year"))
            elif name == "calculate_eclipse_visibility":
                result = await self.calculate_eclipse_visibility(arguments.get("date"), arguments.get("location"))
            elif name == "predict_next_eclipse":
                result = await self.predict_next_eclipse(arguments.get("location"), arguments.get("after_date"))
            else:
                result = {"error": f"Unknown tool '{name}'"}
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    server_instance = EclipseCalculatorServer()
    server_instance.setup_handlers()
    init_options = InitializationOptions(
        server_name="eclipse-calculator-db",
        server_version="2.1.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    async with stdio_server() as (read, write):
        await server_instance.server.run(read, write, init_options)

if __name__ == "__main__":
    print("🌒 Starting Eclipse Calculator MCP Server (DB Version)...", file=sys.stderr, flush=True)
    asyncio.run(main())
