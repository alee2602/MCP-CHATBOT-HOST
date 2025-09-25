TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "read_text_file",
        "description": "Read complete contents of a file as text",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "head": {"type": "number", "description": "First N lines"},
                "tail": {"type": "number", "description": "Last N lines"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file", 
        "description": "Create new file or overwrite existing",
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
        "name": "create_directory",
        "description": "Create new directory or ensure it exists",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": "List directory contents",
        "input_schema": {
            "type": "object", 
            "properties": {
                "path": {"type": "string", "description": "Directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "move_file",
        "description": "Move or rename files and directories",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source path"},
                "destination": {"type": "string", "description": "Destination path"}
            },
            "required": ["source", "destination"]
        }
    }
]