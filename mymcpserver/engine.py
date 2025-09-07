import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

class PlaylistEngine:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.df = None
        self.scaler = StandardScaler()
        self.audio_features = [
            'danceability', 'energy', 'valence', 'acousticness', 
            'instrumentalness', 'liveness', 'speechiness', 'tempo'
        ]
        self._load_dataset()
        
    def _load_dataset(self):
        """Load and preprocess the dataset"""
        try:
            self.df = pd.read_csv(self.dataset_path)
            
            # Basic data cleaning - use correct column names
            self.df = self.df.dropna(subset=['track_name', 'track_artist'])
            
            # Ensure audio features exist with defaults if missing
            for feature in self.audio_features:
                if feature not in self.df.columns:
                    self.df[feature] = 0.5  
            
            # Create a backup copy of original audio features for analysis
            self.original_features = self.df[self.audio_features].copy()
            
            # Normalize audio features for similarity calculations
            audio_data = self.df[self.audio_features].fillna(0.5)
            self.df[self.audio_features] = self.scaler.fit_transform(audio_data)
            
            #print(f"Dataset loaded: {len(self.df)} songs")
            #print(f"Columns available: {list(self.df.columns)}")
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Create empty dataframe as fallback
            self.df = pd.DataFrame()
    
    def create_mood_playlist(self, mood: str, size: int = 10, 
                        genre_filter: Optional[str] = None,
                        min_popularity: int = 0) -> List[Dict]:
        
        # Define mood profiles using valence and energy (using normalized values)
        mood_profiles = {
            'happy': {'valence_min': 0.2, 'energy_min': 0.0},  
            'sad': {'valence_max': -0.2, 'energy_max': 0.0},
            'energetic': {'energy_min': 0.5, 'tempo_min': 0.2},
            'calm': {'energy_max': -0.3, 'acousticness_min': 0.0},
            'party': {'danceability_min': 0.3, 'energy_min': 0.3, 'valence_min': 0.2},
            'chill': {'energy_max': 0.0, 'valence_min': -0.3, 'valence_max': 0.3}
        }
        
        if mood not in mood_profiles:
            return []
        
        filtered_df = self.df.copy()
        
        # Apply popularity filter
        if 'track_popularity' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['track_popularity'] >= min_popularity]
        
        # Apply genre filter
        if genre_filter and 'playlist_genre' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['playlist_genre'].str.contains(genre_filter, case=False, na=False)
            ]
        
        # Apply mood filters
        profile = mood_profiles[mood]
        for feature, threshold in profile.items():
            if feature.endswith('_min') and feature.replace('_min', '') in filtered_df.columns:
                col = feature.replace('_min', '')
                filtered_df = filtered_df[filtered_df[col] >= threshold]
            elif feature.endswith('_max') and feature.replace('_max', '') in filtered_df.columns:
                col = feature.replace('_max', '')
                filtered_df = filtered_df[filtered_df[col] <= threshold]
        
        # Sample random songs from filtered results
        if len(filtered_df) < size:
            selected = filtered_df.copy()
        else:
            selected = filtered_df.sample(n=size)
        
        return self._format_songs_output(selected)
    
    def find_similar_songs(self, reference_song: str, artist: Optional[str] = None, count: int = 5) -> List[Tuple[Dict, float]]:
        """Find songs similar to a reference song using cosine similarity"""
        
        # First try exact match
        query_df = self.df[
            self.df['track_name'].str.contains(reference_song, case=False, na=False)
        ]
        
        # If no results and song name is long, try with first part only
        if query_df.empty and len(reference_song) > 20:
            short_name = reference_song.split(' - ')[0].split(' (')[0][:15]
            query_df = self.df[
                self.df['track_name'].str.contains(short_name, case=False, na=False)
            ]
        
        if artist:
            query_df = query_df[
                query_df['track_artist'].str.contains(artist, case=False, na=False)
            ]
        
        if query_df.empty:
            return []
        
        # Use the first match as reference
        ref_song = query_df.iloc[0]
        ref_features = ref_song[self.audio_features].values.reshape(1, -1)
        
        # Calculate similarities with all songs
        all_features = self.df[self.audio_features].values
        similarities = cosine_similarity(ref_features, all_features)[0]
        
        # Get top similar songs (excluding the reference song itself)
        similar_indices = np.argsort(similarities)[::-1][1:count+1]
        
        results = []
        for idx in similar_indices:
            song_data = self.df.iloc[idx].to_dict()
            similarity_score = similarities[idx]
            results.append((song_data, similarity_score))
        
        return results
    
    def analyze_song(self, song_name: str, artist: Optional[str] = None) -> Optional[Dict]:
        """Get detailed analysis of a specific song"""
        
        # First try exact match with the full song name
        query_df = self.df[
            self.df['track_name'].str.contains(song_name, case=False, na=False)
        ]
        
        # If no results and song name is long, try with first part only
        if query_df.empty and len(song_name) > 20:
            # Try with first 15 characters or until first special character
            short_name = song_name.split(' - ')[0].split(' (')[0][:15]
            query_df = self.df[
                self.df['track_name'].str.contains(short_name, case=False, na=False)
            ]
        
        if artist:
            query_df = query_df[
                query_df['track_artist'].str.contains(artist, case=False, na=False)
            ]
        
        if query_df.empty:
            return None
        
        # Return the song with original (non-normalized) audio features for analysis
        song_dict = query_df.iloc[0].to_dict()
        
        # Replace normalized features with original values for better readability
        song_index = query_df.index[0]
        for feature in self.audio_features:
            if hasattr(self, 'original_features') and feature in self.original_features.columns:
                song_dict[feature] = self.original_features.loc[song_index, feature]
        
        return song_dict
    
    def create_genre_playlist(self, genres: List[str], size: int = 15, 
                            diversity_level: str = "medium") -> List[Dict]:
        """Create a playlist focused on specific genres"""
        
        if 'playlist_genre' not in self.df.columns:
            # If no genre column, return random sample
            return self._format_songs_output(self.df.sample(n=min(size, len(self.df))))
        
        # Filter by genres
        genre_filter = '|'.join(genres)
        filtered_df = self.df[
            self.df['playlist_genre'].str.contains(genre_filter, case=False, na=False)
        ]
        
        if filtered_df.empty:
            return []
        
        # Apply diversity logic
        if diversity_level == "low":
            # More similar songs
            selected = filtered_df.sample(n=min(size, len(filtered_df)))
        elif diversity_level == "high":
            # More diverse selection using audio features
            if len(filtered_df) <= size:
                selected = filtered_df.copy()
            else:
                # Use clustering-like approach for diversity
                features = filtered_df[self.audio_features].values
                # Use simple diversity (select songs with varied feature combinations)
                indices = self._select_diverse_songs(features, size)
                selected = filtered_df.iloc[indices]
        else:  
            selected = filtered_df.sample(n=min(size, len(filtered_df)), random_state=42)
        
        return self._format_songs_output(selected)
    
    def _select_diverse_songs(self, features: np.ndarray, count: int) -> List[int]:
        """Select diverse songs based on feature variance"""
        if len(features) <= count:
            return list(range(len(features)))
        
        selected_indices = [0]  # Start with first song
        remaining_indices = list(range(1, len(features)))
        
        while len(selected_indices) < count and remaining_indices:
            # Calculate average distance from already selected songs
            max_min_distance = -1
            best_idx = None
            
            for candidate_idx in remaining_indices:
                candidate_features = features[candidate_idx]
                
                # Find minimum distance to any selected song
                min_distance = float('inf')
                for selected_idx in selected_indices:
                    distance = np.linalg.norm(candidate_features - features[selected_idx])
                    min_distance = min(min_distance, distance)
                
                # Select song with maximum minimum distance (most diverse)
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_idx = candidate_idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
        
        return selected_indices
    
    def get_dataset_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_songs': len(self.df),
            'unique_artists': self.df['track_artist'].nunique() if 'track_artist' in self.df.columns else 0,
            'unique_albums': self.df['track_album_name'].nunique() if 'track_album_name' in self.df.columns else 0
        }
        
        # Audio feature statistics (using original values)
        original_data = self.original_features if hasattr(self, 'original_features') else self.df
        
        if 'track_popularity' in self.df.columns:
            stats['avg_popularity'] = self.df['track_popularity'].mean()
            stats['popularity_min'] = self.df['track_popularity'].min()
            stats['popularity_max'] = self.df['track_popularity'].max()
        
        for feature in ['energy', 'valence', 'danceability']:
            if feature in original_data.columns:
                stats[f'avg_{feature}'] = original_data[feature].mean()
        
        if 'tempo' in original_data.columns:
            stats['tempo_min'] = original_data['tempo'].min()
            stats['tempo_max'] = original_data['tempo'].max()
            stats['avg_tempo'] = original_data['tempo'].mean()
        
        if 'duration_ms' in self.df.columns:
            stats['avg_duration_minutes'] = (self.df['duration_ms'].mean() / 1000 / 60)
        
        # Genre statistics
        if 'playlist_genre' in self.df.columns:
            genre_counts = self.df['playlist_genre'].value_counts().head(10)
            stats['top_genres'] = list(zip(genre_counts.index, genre_counts.values))
        
        # Subgenre statistics
        if 'playlist_subgenre' in self.df.columns:
            subgenre_counts = self.df['playlist_subgenre'].value_counts().head(5)
            stats['top_subgenres'] = list(zip(subgenre_counts.index, subgenre_counts.values))
        
        return stats
    
    def _format_songs_output(self, songs_df: pd.DataFrame) -> List[Dict]:
        """Format songs dataframe for output"""
        if songs_df.empty:
            return []
        
        # Convert to list of dictionaries with essential info
        songs_list = []
        for idx, song in songs_df.iterrows():
            # Use original features for display
            original_features = {}
            if hasattr(self, 'original_features'):
                for feature in self.audio_features:
                    if feature in self.original_features.columns:
                        original_features[feature] = self.original_features.loc[idx, feature]
            
            song_dict = {
                'name': song.get('track_name', 'Unknown'),
                'artists': song.get('track_artist', 'Unknown Artist'),
                'album': song.get('track_album_name', 'Unknown Album'),
                'genre': song.get('playlist_genre', 'Unknown'),
                'subgenre': song.get('playlist_subgenre', 'Unknown'),
                'popularity': song.get('track_popularity', 'N/A'),
                'energy': original_features.get('energy', song.get('energy', 0)),
                'valence': original_features.get('valence', song.get('valence', 0)),
                'danceability': original_features.get('danceability', song.get('danceability', 0)),
                'acousticness': original_features.get('acousticness', song.get('acousticness', 0)),
                'tempo': original_features.get('tempo', song.get('tempo', 120)),
                'duration_minutes': song.get('duration_ms', 0) / 1000 / 60 if song.get('duration_ms') else 0
            }
            songs_list.append(song_dict)
        
        return songs_list