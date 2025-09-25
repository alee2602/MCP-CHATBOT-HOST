TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "create_repository",
        "description": "Create a new GitHub repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "private": {"type": "boolean"},
                "autoInit": {"type": "boolean"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "create_branch",
        "description": "Create a new branch from another branch",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "branch": {"type": "string"},
                "from_branch": {"type": "string"}
            },
            "required": ["owner", "repo", "branch"]
        }
    },
    {
        "name": "search_repositories",
        "description": "Search for GitHub repositories",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "page": {"type": "number"},
                "perPage": {"type": "number"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_issue",
        "description": "Create a new issue in a repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "assignees": {"type": "array", "items": {"type": "string"}},
                "labels": {"type": "array", "items": {"type": "string"}},
                "milestone": {"type": "number"}
            },
            "required": ["owner", "repo", "title"]
        }
    },
    {
        "name": "list_issues",
        "description": "List and filter issues in a repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
                "sort": {"type": "string"},
                "direction": {"type": "string"},
                "since": {"type": "string"},
                "page": {"type": "number"},
                "per_page": {"type": "number"}
            },
            "required": ["owner", "repo"]
        }
    },
    {
        "name": "update_issue",
        "description": "Update an existing issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "issue_number": {"type": "number"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "state": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
                "assignees": {"type": "array", "items": {"type": "string"}},
                "milestone": {"type": "number"}
            },
            "required": ["owner", "repo", "issue_number"]
        }
    },
    {
        "name": "add_issue_comment",
        "description": "Add a comment to an issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "issue_number": {"type": "number"},
                "body": {"type": "string"}
            },
            "required": ["owner", "repo", "issue_number", "body"]
        }
    },
    {
        "name": "create_pull_request",
        "description": "Create a pull request",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "head": {"type": "string"},
                "base": {"type": "string"},
                "draft": {"type": "boolean"},
                "maintainer_can_modify": {"type": "boolean"}
            },
            "required": ["owner", "repo", "title", "head", "base"]
        }
    },
    {
        "name": "merge_pull_request",
        "description": "Merge a pull request",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "pull_number": {"type": "number"},
                "commit_title": {"type": "string"},
                "commit_message": {"type": "string"},
                "merge_method": {"type": "string", "enum": ["merge", "squash", "rebase"]}
            },
            "required": ["owner", "repo", "pull_number"]
        }
    }
]
