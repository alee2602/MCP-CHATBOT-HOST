TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "hex_to_rgb",
        "description": "Convert HEX color to RGB values",
        "input_schema": {
            "type": "object",
            "properties": {
                "hex_color": {"type": "string", "description": "HEX color (e.g., #FF0000 or FF0000)"}
            },
            "required": ["hex_color"]
        }
    },
    {
        "name": "rgb_to_hex", 
        "description": "Convert RGB values to HEX color",
        "input_schema": {
            "type": "object",
            "properties": {
                "r": {"type": "integer", "minimum": 0, "maximum": 255},
                "g": {"type": "integer", "minimum": 0, "maximum": 255},
                "b": {"type": "integer", "minimum": 0, "maximum": 255}
            },
            "required": ["r", "g", "b"]
        }
    },
    {
        "name": "random_color",
        "description": "Generate a random color",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "color_palette",
        "description": "Generate color palette",
        "input_schema": {
            "type": "object",
            "properties": {
                "base_color": {"type": "string", "description": "Base HEX color"},
                "palette_type": {"type": "string", "enum": ["complementary", "triadic", "analogous"], "default": "complementary"}
            },
            "required": ["base_color"]
        }
    }
]