# Configuración para Eclipse MCP Server

TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "list_eclipses_by_year",
        "description": "List all known eclipses for a given year",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Year to search for eclipses"}
            },
            "required": ["year"]
        }
    },
    {
        "name": "calculate_eclipse_visibility",
        "description": "Calculate eclipse visibility for a date and location",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "location": {"type": "string", "description": "Location name (e.g., Guatemala City, Madrid, Sydney)"}
            },
            "required": ["date", "location"]
        }
    },
    {
        "name": "predict_next_eclipse",
        "description": "Predict next visible eclipse for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Location name"},
                "after_date": {"type": "string", "description": "Date after which to search (YYYY-MM-DD format)"}
            },
            "required": ["location"]
        }
    }
]