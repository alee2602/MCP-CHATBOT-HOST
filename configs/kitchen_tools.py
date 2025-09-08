# Configuración para Kitchen MCP Server

TOOL_CONFIGS = {}

ANTHROPIC_TOOLS = [
    {
        "name": "recommend_by_mood_and_season",
        "description": "Recommend foods or recipes based on mood and season",
        "input_schema": {
            "type": "object",
            "properties": {
                "mood": {"type": "string", "description": "Mood (happy, excited, tender, scared, angry, sad)"},
                "season": {"type": "string", "description": "Season (spring, summer, autumn, winter)"},
                "type": {"type": "string", "description": "Type: food or recipe"}
            },
            "required": ["mood"]
        }
    },
    {
        "name": "suggest_recipe_by_diet",
        "description": "Suggest recipes by diet type",
        "input_schema": {
            "type": "object",
            "properties": {
                "diet": {"type": "string", "description": "Diet type (vegan, keto, mediterranean, paleo, dash)"},
                "maxCalories": {"type": "number", "description": "Maximum calories"}
            },
            "required": ["diet"]
        }
    },
    {
        "name": "get_recipes_by_ingredients",
        "description": "Find recipes by ingredients",
        "input_schema": {
            "type": "object",
            "properties": {
                "ingredients": {"type": "array", "items": {"type": "string"}, "description": "List of ingredients"}
            },
            "required": ["ingredients"]
        }
    },
    {
        "name": "suggest_ingredient_substitution",
        "description": "Suggest ingredient substitutes",
        "input_schema": {
            "type": "object",
            "properties": {
                "ingredient": {"type": "string", "description": "Ingredient to substitute"}
            },
            "required": ["ingredient"]
        }
    },
    {
        "name": "get_food_by_name",
        "description": "Find specific food by name",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Food name to search"}
            },
            "required": ["name"]
        }
    }
]