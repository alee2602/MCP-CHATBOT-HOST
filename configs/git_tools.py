TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "git_init",
        "description": "Initializes a new Git repository at the given absolute path",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to initialize"},
                "initialBranch": {"type": "string", "description": "Initial branch name (e.g., 'main')"},
                "bare": {"type": "boolean", "description": "Create a bare repository"},
                "quiet": {"type": "boolean", "description": "Suppress output"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "git_remote",
        "description": "Manages remote repositories (list, add, remove, show, set-url)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"},
                "mode": {
                    "type": "string",
                    "enum": ["list", "add", "remove", "show", "set-url"],
                    "description": "Remote operation mode"
                },
                "name": {"type": "string", "description": "Remote name (e.g., 'origin')"},
                "url": {"type": "string", "description": "Remote URL (SSH or HTTPS)"}
            },
            "required": ["mode"]
        }
    },
    {
        "name": "git_branch",
        "description": "Manages branches (list, create, delete, rename, show current)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"},
                "mode": {
                    "type": "string", 
                    "enum": ["list", "create", "delete", "rename", "show"],
                    "description": "Branch operation mode"
                },
                "branchName": {"type": "string", "description": "Branch name"},
                "newBranchName": {"type": "string", "description": "New branch name for rename"},
                "startPoint": {"type": "string", "description": "Starting point for new branch"},
                "force": {"type": "boolean", "description": "Force operation"},
                "all": {"type": "boolean", "description": "Show all branches"},
                "remote": {"type": "boolean", "description": "Show remote branches"}
            },
            "required": ["mode"]
        }
    },
    {
        "name": "git_add",
        "description": "Stages specified files or patterns",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to add"}
            },
            "required": ["files"]
        }
    },
    {
        "name": "git_commit",
        "description": "Commits staged changes",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"},
                "message": {"type": "string", "description": "Commit message"},
                "author": {"type": "string", "description": "Author override"},
                "allowEmpty": {"type": "boolean", "description": "Allow empty commit"},
                "amend": {"type": "boolean", "description": "Amend previous commit"},
                "forceUnsignedOnFailure": {"type": "boolean", "description": "Force unsigned on failure"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "git_push",
        "description": "Updates remote refs using local refs",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Working directory path"},
                "remote": {"type": "string", "description": "Remote name"},
                "branch": {"type": "string", "description": "Branch name"},
                "remoteBranch": {"type": "string", "description": "Remote branch name"},
                "force": {"type": "boolean", "description": "Force push"},
                "forceWithLease": {"type": "boolean", "description": "Force with lease"},
                "setUpstream": {"type": "boolean", "description": "Set upstream"},
                "tags": {"type": "boolean", "description": "Push tags"},
                "delete": {"type": "boolean", "description": "Delete branch"}
            },
            "required": []
        }
    },
    {
    "name": "git_status",
    "description": "Gets repository status (branch, staged, modified, untracked files)",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Working directory path"}
        },
        "required": [] 
    }
},
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
    "name": "git_checkout",
    "description": "Switches branches or restores working tree files",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Working directory path"},
            "branchOrPath": {"type": "string", "description": "Branch name or file path"},
            "newBranch": {"type": "boolean", "description": "Create new branch"},
            "force": {"type": "boolean", "description": "Force checkout"}
        },
        "required": ["branchOrPath"]
    }
}
]