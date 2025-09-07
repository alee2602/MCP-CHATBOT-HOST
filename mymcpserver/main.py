#!/usr/bin/env python3
import asyncio
import json
import sys
import os
from engine import PlaylistEngine
from typing import List

class MCPServer:
    def __init__(self):
        print("Initializing MCPServer...", file=sys.stderr)
        self.playlist_engine = None  
        
        try:
            dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spotify_songs.csv")
            print(f"Looking for dataset: {dataset_path}", file=sys.stderr)
            print(f"Full path: {os.path.abspath(dataset_path)}", file=sys.stderr)
            print(f"Dataset exists: {os.path.exists(dataset_path)}", file=sys.stderr)
            
            if not os.path.exists(dataset_path):
                raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
            print("Creating PlaylistEngine...", file=sys.stderr)
            self.playlist_engine = PlaylistEngine(dataset_path)
            print("PlaylistEngine created successfully!", file=sys.stderr)
            
        except Exception as e:
            print(f"ERROR in MCPServer.__init__: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise  # Re-lanzar la excepción para que main() la pueda manejar
        
    async def handle_request(self, request):
        """Maneja requests JSON-RPC"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "mcp-playlist",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "create_mood_playlist",
                        "description": "Create a playlist based on mood and preferences",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "mood": {"type": "string", "description": "The mood for the playlist"},
                                "size": {"type": "integer", "default": 10},
                                "genre": {"type": "string", "description": "Optional genre filter"},
                                "min_popularity": {"type": "integer", "default": 0}
                            },
                            "required": ["mood"]
                        }
                    },
                    {
                        "name": "find_similar_songs",
                        "description": "Find songs similar to a reference song",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "song_name": {"type": "string"},
                                "artist": {"type": "string"},
                                "count": {"type": "integer", "default": 5}
                            },
                            "required": ["song_name"]
                        }
                    },
                    {
                        "name": "analyze_song",
                        "description": "Get detailed audio feature analysis of a song",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "song_name": {"type": "string"},
                                "artist": {"type": "string"}
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
                                "genres": {"type": "array", "items": {"type": "string"}},
                                "size": {"type": "integer", "default": 15},
                                "diversity": {"type": "string", "default": "medium"}
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
            }
        
        elif method == "tools/call":
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
                    result = self.get_dataset_stats(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return {"content": [{"type": "text", "text": result}]}
                
            except Exception as e:
                raise Exception(f"Error executing {tool_name}: {str(e)}")
        
        else:
            raise ValueError(f"Unknown method: {method}")

    def create_mood_playlist(self, mood: str, size: int = 10, genre: str = None, min_popularity: int = 0) -> str:
        """Create a playlist based on mood and preferences"""
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

    def find_similar_songs(self, song_name: str, artist: str = None, count: int = 5) -> str:
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

    def analyze_song(self, song_name: str, artist: str = None) -> str:
        """Get detailed audio feature analysis of a song"""
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
            
            result = f"🎸 **Genre Playlist: {', '.join(genres)}** ({len(playlist)} songs)\n\n"
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
    
    print(f"Dataset loaded: {len(server.playlist_engine.df)} songs", file=sys.stderr)
    
    def read_exactly(n):
        """Lee exactamente n caracteres de stdin"""
        chars = []
        for _ in range(n):
            char = sys.stdin.read(1)
            if not char:
                break
            chars.append(char)
        return ''.join(chars)
    
    while True:
        try:
            line = input()
            if not line:
                continue
                
            print(f"Received line: {line}", file=sys.stderr)
                
            # Parse Content-Length header
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
                print(f"Content length: {content_length}", file=sys.stderr)
                
                # Read empty line
                empty_line = input()
                print(f"Empty line: '{empty_line}'", file=sys.stderr)
                
                # Read JSON message
                message = read_exactly(content_length)
                print(f"Received message: {message}", file=sys.stderr)
                
                try:
                    request = json.loads(message)
                    request_id = request.get("id")
                    
                    print(f"Processing method: {request.get('method')}", file=sys.stderr)
                    
                    try:
                        result = await server.handle_request(request)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    except Exception as e:
                        print(f"Error handling request: {e}", file=sys.stderr)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            }
                        }
                    
                    # Send response with Content-Length header
                    response_json = json.dumps(response)
                    output = f"Content-Length: {len(response_json)}\r\n\r\n{response_json}"
                    print(output, end="", flush=True)
                    print(f"Sent response: {response_json}", file=sys.stderr)
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}", file=sys.stderr)
                    # Send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    response_json = json.dumps(error_response)
                    output = f"Content-Length: {len(response_json)}\r\n\r\n{response_json}"
                    print(output, end="", flush=True)
                    
        except EOFError:
            print("EOF received", file=sys.stderr)
            break
        except Exception as e:
            # Log error to stderr
            print(f"Server error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())