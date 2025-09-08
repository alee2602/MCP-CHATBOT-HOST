TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "git_set_working_dir",
        "description": "Set git working directory", 
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "git_status",
        "description": "Show git status",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "git_add", 
        "description": "Add files to staging",
        "input_schema": {
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to add"}
            },
            "required": ["files"]
        }
    },
    {
        "name": "git_commit",
        "description": "Create commit",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "git_push",
        "description": "Push commits to remote repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "Remote name", "default": "origin"},
                "branch": {"type": "string", "description": "Branch name", "default": "main"}
            },
            "required": []
        }
    }
]