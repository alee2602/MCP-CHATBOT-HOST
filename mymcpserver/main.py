from fastmcp import FastMCP
from engine import PlaylistEngine
from typing import List, Dict, Any, Optional, Tuple
import os

# Initialize FastMCP server
mcp = FastMCP("mcp-playlist")

# Initialize playlist engine
dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spotify_songs.csv")
playlist_engine = PlaylistEngine(dataset_path)

@mcp.tool()
def create_mood_playlist(mood: str, size: int = 10, genre: str = None, min_popularity: int = 0, duration_minutes: float = None,) -> str:
    """
        Create a playlist based on mood and preferences.

        You can specify EITHER:
        - size (number of songs), OR
        - duration_minutes (target total duration in minutes).

        Optional filters:
        - genre (e.g., pop, rock)
        - min_popularity: 0-100
        """
    try:
        # --- Duration-based selection---
        if duration_minutes and duration_minutes > 0:
            # Grab a generous pool for better packing; engine will cap if dataset is small
            pool_size = max(size * 5, 200)
            pool = playlist_engine.create_mood_playlist(
                mood=mood,
                size=pool_size,
                genre_filter=genre,          
                min_popularity=min_popularity,
            )

            # Keep only tracks with valid durations
            pool = [s for s in pool if (s.get("duration_minutes") or 0) > 0]
            if not pool:
                return f"No songs found for mood '{mood}' with the specified filters."

            # shortest-first to approach the target time
            pool.sort(key=lambda s: s["duration_minutes"])
            target = float(duration_minutes)
            total = 0.0
            chosen: List[dict] = []
            for song in pool:
                d = float(song.get("duration_minutes", 0) or 0)
                if d <= 0:
                    continue
                if total + d <= target + 0.5:   
                    chosen.append(song)
                    total += d
                if total >= target - 0.5:
                    break

            if not chosen:
                # If every track is longer than target, return the shortest one
                chosen = [pool[0]]
                total = float(pool[0]["duration_minutes"])

            result = f"**{mood.title()} Mood Playlist** (~{total:.1f} min, target {target:.1f})\n\n"
            for i, song in enumerate(chosen, 1):
                result += f"{i}. **{song.get('name','Unknown')}** by {song.get('artists','Unknown Artist')}\n"
                result += f"   Genre: {song.get('genre','Unknown')} | "
                result += f"Popularity: {song.get('popularity','N/A')} | "
                result += f"Energy: {song.get('energy', 0):.2f} | "
                result += f"Duration: {song.get('duration_minutes', 0):.1f} min\n\n"
            return result

        # --- Size-based selection ---
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
            result += f"{i}. **{song.get('name','Unknown')}** by {song.get('artists','Unknown Artist')}\n"
            result += f"   Genre: {song.get('genre','Unknown')} | "
            result += f"Popularity: {song.get('popularity','N/A')} | "
            result += f"Energy: {song.get('energy', 0):.2f}"
            if song.get("duration_minutes"):
                result += f" | Duration: {song['duration_minutes']:.1f} min"
            result += "\n\n"
        return result

    except Exception as e:
        return f"Error creating mood playlist: {str(e)}"

@mcp.tool()
def find_similar_songs(song_name: str, artist: str = None, count: int = 5) -> str:
    """
    Find songs similar to a reference song based on audio features.
    - Excludes the same track (same title+artist) and deduplicates versions.
    """
    try:
        # Oversample to allow dedup without losing requested count
        raw: List[Tuple[Dict[str, Any], float]] = playlist_engine.find_similar_songs(
            reference_song=song_name,   # engine expects reference_song
            artist=artist,
            count=max(count * 5, count + 10)
        )

        if not raw:
            return f"Song '{song_name}' not found in dataset."

        # Normalize reference keys
        ref_name = (song_name or "").strip().lower()
        ref_artist = (artist or "").strip().lower()

        def key_of(s: Dict[str, Any]) -> str:
            name = (s.get("track_name") or s.get("name") or "").strip().lower()
            art = (s.get("track_artist") or s.get("artists") or "").strip().lower()
            return f"{name}||{art}"

        def is_same_song(s: Dict[str, Any]) -> bool:
            name = (s.get("track_name") or s.get("name") or "").strip().lower()
            art = (s.get("track_artist") or s.get("artists") or "").strip().lower()
            # exclude exact match on both title and (when provided) artist
            if ref_artist:
                return (name == ref_name) and (art == ref_artist)
            return (name == ref_name)

        seen: set[str] = set()
        filtered: List[Tuple[Dict[str, Any], float]] = []

        for item in raw:
            s, sim = item if isinstance(item, tuple) else (item, 0.0)
            if is_same_song(s):
                # skip the reference track itself (often appears with sim=1.0)
                continue
            k = key_of(s)
            if k in seen:
                # skip duplicate versions of the exact same title+artist
                continue
            seen.add(k)
            filtered.append((s, sim))
            if len(filtered) >= count:
                break

        if not filtered:
            return f"No similar songs found for '{song_name}'."

        result = f"**Songs similar to '{song_name}'**\n\n"
        for i, (song, similarity) in enumerate(filtered, 1):
            name = song.get("track_name", "Unknown")
            art = song.get("track_artist", "Unknown Artist")
            genre = song.get("playlist_genre", "Unknown")
            result += f"{i}. **{name}** by {art}\n"
            result += f"   Similarity: {similarity:.3f} | Genre: {genre}\n\n"
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
        
        result = f" **Genre Playlist: {', '.join(genres)}** ({len(playlist)} songs)\n\n"
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