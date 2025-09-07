TOOL_CONFIGS = {
    "analyze_song": {
        "song_name": "song_name",
        "artist": "artist",
    },
    "find_similar_songs": {
        "song_name": "song_name",
        "artist": "artist",
        "count": "count",
    },
    "create_mood_playlist": {
        "mood": "mood",
        "size": "size",
        "genre": "genre",
        "min_popularity": "min_popularity",
        "duration_minutes": "duration_minutes",  
    },
    "create_genre_playlist": {
        "genres": "genres",
        "size": "size",
        "diversity": "diversity",
    },
    "get_dataset_stats": {},
}

ANTHROPIC_TOOLS = [
    {
        "name": "get_dataset_stats",
        "description": "Get comprehensive statistics about the music dataset",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "analyze_song",
        "description": "Analyze audio features of a specific song",
        "input_schema": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string", "description": "Name of the song"},
                "artist": {"type": "string", "description": "Artist name (optional)"},
            },
            "required": ["song_name"],
        },
    },
    {
        "name": "find_similar_songs",
        "description": "Find songs similar to a reference song",
        "input_schema": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string", "description": "Reference song name"},
                "artist": {"type": "string", "description": "Artist name (optional)"},
                "count": {"type": "integer", "description": "How many similar songs", "default": 5},
            },
            "required": ["song_name"],
        },
    },
    {
        "name": "create_mood_playlist",
        "description": "Create a playlist from the dataset for a given mood. You can specify either 'size' or 'duration_minutes'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mood": {
                    "type": "string",
                    "description": "Mood (happy, sad, energetic, calm, party, chill)",
                },
                "size": {"type": "integer", "description": "Number of songs", "default": 10},
                "duration_minutes": {
                    "type": "number",
                    "description": "Target total duration in minutes (alternative to size)",
                },
                "genre": {"type": "string", "description": "Optional genre filter (e.g., pop, rock)"},
                "min_popularity": {
                    "type": "integer",
                    "description": "Minimum popularity score (0-100)",
                    "default": 0,
                },
            },
            "required": ["mood"],
        },
    },
    {
        "name": "create_genre_playlist",
        "description": "Create a playlist focused on specific genres",
        "input_schema": {
            "type": "object",
            "properties": {
                "genres": {"type": "array", "items": {"type": "string"}, "description": "List of genres"},
                "size": {"type": "integer", "description": "Number of songs", "default": 15},
                "diversity": {
                    "type": "string",
                    "description": "Diversity level (low, medium, high)",
                    "default": "medium",
                },
            },
            "required": ["genres"],
        },
    },
]
