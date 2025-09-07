from fastmcp import FastMCP
from engine import PlaylistEngine
from typing import List
import os

# Initialize FastMCP server
mcp = FastMCP("mcp-playlist")

# Initialize playlist engine
dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spotify_songs.csv")
playlist_engine = PlaylistEngine(dataset_path)

@mcp.tool()
def create_mood_playlist(mood: str, size: int = 10, genre: str = None, min_popularity: int = 0) -> str:
    """
    Create a playlist based on mood and preferences
    
    Args:
        mood: The mood for the playlist (happy, sad, energetic, calm, party, chill)
        size: Number of songs in the playlist (default: 10)
        genre: Optional genre filter (e.g., pop, rock, edm, rap, latin)
        min_popularity: Minimum popularity score (0-100)
    
    Returns:
        Formatted playlist as a string
    """
    try:
        playlist = playlist_engine.create_mood_playlist(
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

@mcp.tool()
def find_similar_songs(song_name: str, artist: str = None, count: int = 5) -> str:
    """
    Find songs similar to a reference song based on audio features
    
    Args:
        song_name: Name of the reference song
        artist: Artist name (optional, helps with accuracy)
        count: Number of similar songs to return (default: 5)
    
    Returns:
        List of similar songs with similarity scores
    """
    try:
        similar_songs = playlist_engine.find_similar_songs(
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

@mcp.tool()
def analyze_song(song_name: str, artist: str = None) -> str:
    """
    Get detailed audio feature analysis of a specific song
    
    Args:
        song_name: Name of the song to analyze
        artist: Artist name (optional, helps with accuracy)
    
    Returns:
        Detailed analysis of the song's audio features
    """
    try:
        analysis = playlist_engine.analyze_song(song_name, artist)
        
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

@mcp.tool()
def create_genre_playlist(genres: List[str], size: int = 15, diversity: str = "medium") -> str:
    """
    Create a playlist focused on specific genres
    
    Args:
        genres: List of genres to include (edm, rap, pop, r&b, latin, rock)
        size: Number of songs in the playlist (default: 15)
        diversity: Diversity level - low, medium, high (default: medium)
    
    Returns:
        Formatted genre-based playlist
    """
    try:
        playlist = playlist_engine.create_genre_playlist(
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

@mcp.tool()
def get_dataset_stats() -> str:
    """
    Get comprehensive statistics about the music dataset
    
    Returns:
        Detailed statistics about the dataset
    """
    try:
        stats = playlist_engine.get_dataset_statistics()
        
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

# Run the server
if __name__ == "__main__":
    mcp.run()