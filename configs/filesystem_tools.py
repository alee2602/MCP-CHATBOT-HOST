TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "read_file",
        "description": "Read file content",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file", 
        "description": "Write content to file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "File content"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List directory contents",
        "input_schema": {
            "type": "object", 
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."}
            },
            "required": []
        }
    }
]