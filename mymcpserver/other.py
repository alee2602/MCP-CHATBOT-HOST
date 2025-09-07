#!/usr/bin/env python3
"""
Standard MCP Server for Playlist Curator
Compatible with any MCP client that follows the protocol specification
"""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any, Optional
from engine import PlaylistEngine

class MCPServer:
    def __init__(self):
        # Initialize playlist engine
        dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spotify_songs.csv")
        self.playlist_engine = PlaylistEngine(dataset_path)
        self.initialized = False
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            if method == "initialize":
                return await self.handle_initialize(req_id, params)
            elif method == "tools/list":
                return await self.handle_tools_list(req_id)
            elif method == "tools/call":
                return await self.handle_tools_call(req_id, params)
            elif method == "ping":
                return {"jsonrpc": "2.0", "id": req_id, "result": "pong"}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def handle_initialize(self, req_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        self.initialized = True
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "playlist-curator",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_tools_list(self, req_id: int) -> Dict[str, Any]:
        """Return list of available tools"""
        tools = [
            {
                "name": "create_mood_playlist",
                "description": "Create a playlist based on mood and preferences",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mood": {
                            "type": "string",
                            "enum": ["happy", "sad", "energetic", "calm", "party", "chill"],
                            "description": "The mood for the playlist"
                        },
                        "size": {
                            "type": "integer",
                            "description": "Number of songs in playlist",
                            "default": 10
                        },
                        "genre": {
                            "type": "string",
                            "description": "Optional genre filter"
                        },
                        "min_popularity": {
                            "type": "integer",
                            "description": "Minimum popularity score (0-100)",
                            "default": 0
                        }
                    },
                    "required": ["mood"]
                }
            },
            {
                "name": "find_similar_songs",
                "description": "Find songs similar to a reference song based on audio features",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "song_name": {
                            "type": "string",
                            "description": "Name of the reference song"
                        },
                        "artist": {
                            "type": "string",
                            "description": "Artist name (optional)"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of similar songs to return",
                            "default": 5
                        }
                    },
                    "required": ["song_name"]
                }
            },
            {
                "name": "analyze_song",
                "description": "Get detailed audio feature analysis of a specific song",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "song_name": {
                            "type": "string",
                            "description": "Name of the song to analyze"
                        },
                        "artist": {
                            "type": "string",
                            "description": "Artist name (optional)"
                        }
                    },
                    "required": ["song_name"]
                }
            },
            {
                "name": "create_genre_playlist",
                "description": "Create a playlist focused on specific genres",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "genres": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of genres to include"
                        },
                        "size": {
                            "type": "integer",
                            "description": "Number of songs",
                            "default": 15
                        },
                        "diversity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Diversity level",
                            "default": "medium"
                        }
                    },
                    "required": ["genres"]
                }
            },
            {
                "name": "get_dataset_stats",
                "description": "Get comprehensive statistics about the music dataset",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools}
        }
    
    async def handle_tools_call(self, req_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "create_mood_playlist":
                result = self.create_mood_playlist(**arguments)
            elif tool_name == "find_similar_songs":
                result = self.find_similar_songs(**arguments)
            elif tool_name == "analyze_song":
                result = self.analyze_song(**arguments)
            elif tool_name == "create_genre_playlist":
                result = self.create_genre_playlist(**arguments)
            elif tool_name == "get_dataset_stats":
                result = self.get_dataset_stats()
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": [{"type": "text", "text": result}]
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    def create_mood_playlist(self, mood: str, size: int = 10, genre: Optional[str] = None, min_popularity: int = 0) -> str:
        """Create a playlist based on mood"""
        try:
            playlist = self.playlist_engine.create_mood_playlist(
                mood=mood,
                size=size,
                genre_filter=genre,
                min_popularity=min_popularity
            )
            
            if not playlist:
                return f"No songs found for mood '{mood}' with the specified filters."
            
            result = f"**{mood.title()} Mood Playlist** ({len(playlist)} songs)\n\n"
            for i, song in enumerate(playlist, 1):
                result += f"{i}. **{song['name']}** by {song['artists']}\n"
                result += f"   Genre: {song.get('genre', 'Unknown')} | "
                result += f"Popularity: {song.get('popularity', 'N/A')} | "
                result += f"Energy: {song.get('energy', 0):.2f}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error creating mood playlist: {str(e)}"
    
    def find_similar_songs(self, song_name: str, artist: Optional[str] = None, count: int = 5) -> str:
        """Find songs similar to a reference song"""
        try:
            similar_songs = self.playlist_engine.find_similar_songs(
                reference_song=song_name,
                artist=artist,
                count=count
            )
            
            if not similar_songs:
                return f"Song '{song_name}' not found in dataset."
            
            result = f"**Songs similar to '{song_name}'**\n\n"
            for i, (song, similarity) in enumerate(similar_songs, 1):
                result += f"{i}. **{song['track_name']}** by {song['track_artist']}\n"
                result += f"   Similarity: {similarity:.3f} | Genre: {song.get('playlist_genre', 'Unknown')}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error finding similar songs: {str(e)}"
    
    def analyze_song(self, song_name: str, artist: Optional[str] = None) -> str:
        """Analyze audio features of a specific song"""
        try:
            analysis = self.playlist_engine.analyze_song(song_name, artist)
            
            if not analysis:
                return f"Song '{song_name}' not found in dataset."
            
            song = analysis
            result = f"**Analysis for '{song['track_name']}' by {song['track_artist']}**\n\n"
            result += f"**Audio Features:**\n"
            result += f"• Energy: {song.get('energy', 0):.3f}/1.0\n"
            result += f"• Valence (Mood): {song.get('valence', 0):.3f}/1.0\n"
            result += f"• Danceability: {song.get('danceability', 0):.3f}/1.0\n"
            result += f"• Acousticness: {song.get('acousticness', 0):.3f}/1.0\n"
            result += f"• Instrumentalness: {song.get('instrumentalness', 0):.3f}/1.0\n"
            result += f"• Speechiness: {song.get('speechiness', 0):.3f}/1.0\n"
            result += f"• Liveness: {song.get('liveness', 0):.3f}/1.0\n\n"
            result += f"**Technical Info:**\n"
            result += f"• Tempo: {song.get('tempo', 0):.1f} BPM\n"
            result += f"• Key: {song.get('key', 'Unknown')}\n"
            result += f"• Mode: {song.get('mode', 'Unknown')}\n"
            result += f"• Loudness: {song.get('loudness', 0):.1f} dB\n"
            result += f"• Duration: {song.get('duration_ms', 0)/1000:.1f} seconds\n\n"
            result += f"**Metadata:**\n"
            result += f"• Popularity: {song.get('track_popularity', 'N/A')}/100\n"
            result += f"• Genre: {song.get('playlist_genre', 'Unknown')}\n"
            result += f"• Album: {song.get('track_album_name', 'Unknown')}\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing song: {str(e)}"
    
    def create_genre_playlist(self, genres: List[str], size: int = 15, diversity: str = "medium") -> str:
        """Create a playlist focused on specific genres"""
        try:
            playlist = self.playlist_engine.create_genre_playlist(
                genres=genres,
                size=size,
                diversity_level=diversity
            )
            
            if not playlist:
                return f"No songs found for genres: {', '.join(genres)}"
            
            result = f"**Genre Playlist: {', '.join(genres)}** ({len(playlist)} songs)\n\n"
            for i, song in enumerate(playlist, 1):
                result += f"{i}. **{song['name']}** by {song['artists']}\n"
                result += f"   Genre: {song.get('genre', 'Unknown')} | "
                result += f"Popularity: {song.get('popularity', 'N/A')}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error creating genre playlist: {str(e)}"
    
    def get_dataset_stats(self) -> str:
        """Get comprehensive statistics about the music dataset"""
        try:
            stats = self.playlist_engine.get_dataset_statistics()
            
            result = f"**Dataset Statistics**\n\n"
            result += f"• Total songs: {stats['total_songs']:,}\n"
            result += f"• Unique artists: {stats['unique_artists']:,}\n"
            result += f"• Unique albums: {stats['unique_albums']:,}\n"
            result += f"• Average popularity: {stats.get('avg_popularity', 0):.1f}/100\n"
            result += f"• Average energy: {stats.get('avg_energy', 0):.3f}/1.0\n"
            result += f"• Average valence: {stats.get('avg_valence', 0):.3f}/1.0\n"
            result += f"• Tempo range: {stats.get('tempo_min', 0):.0f} - {stats.get('tempo_max', 200):.0f} BPM\n\n"
            
            if 'top_genres' in stats:
                result += f"**Top 10 Genres:**\n"
                for genre, count in stats['top_genres'][:10]:
                    result += f"• {genre}: {count:,} songs\n"
            
            if 'top_subgenres' in stats:
                result += f"\n**Top 5 Subgenres:**\n"
                for subgenre, count in stats['top_subgenres'][:5]:
                    result += f"• {subgenre}: {count:,} songs\n"
            
            return result
            
        except Exception as e:
            return f"Error getting dataset statistics: {str(e)}"

async def main():
    """Main server loop"""
    server = MCPServer()
    
    # Log to stderr so it doesn't interfere with STDIO protocol
    print("Playlist Curator MCP Server starting...", file=sys.stderr)
    print("Waiting for client connections via STDIO", file=sys.stderr)
    
    while True:
        try:
            # Read Content-Length header
            header = ""
            while True:
                char = sys.stdin.read(1)
                if not char:
                    return
                header += char
                if header.endswith("\r\n\r\n"):
                    break
            
            # Parse content length
            content_length = None
            for line in header.split("\r\n"):
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())
                    break
            
            if content_length is None:
                continue
            
            # Read message body
            message = sys.stdin.read(content_length)
            request = json.loads(message)
            
            print(f"Received request: {request.get('method')}", file=sys.stderr)
            
            # Handle request
            response = await server.handle_request(request)
            
            # Send response
            response_json = json.dumps(response)
            response_content = f"Content-Length: {len(response_json)}\r\n\r\n{response_json}"
            
            sys.stdout.write(response_content)
            sys.stdout.flush()
            
            print(f"Sent response for request {response.get('id')}", file=sys.stderr)
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            # Send error response if possible
            try:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                error_json = json.dumps(error_response)
                error_content = f"Content-Length: {len(error_json)}\r\n\r\n{error_json}"
                sys.stdout.write(error_content)
                sys.stdout.flush()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())