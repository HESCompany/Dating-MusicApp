from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import random

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced dummy dataset
def create_music_dataset():
    return {
        'song_id': range(1, 51),
        'title': [f'Song {i}' for i in range(1, 51)],
        'artist': [f'Artist {i}' for i in range(1, 51)],
        'tempo': np.random.randint(60, 180, 50),
        'energy': np.random.random(50),
        'danceability': np.random.random(50),
        'popularity': np.random.randint(0, 100, 50),
        'release_year': np.random.randint(1990, 2024, 50),
        'genre': np.random.choice(['rock', 'pop', 'jazz', 'electronic', 'classical', 'hip-hop'], 50),
        'mood': np.random.choice(['happy', 'sad', 'energetic', 'calm', 'aggressive'], 50)
    }

# Enhanced user dataset
def create_user_dataset():
    users = []
    for i in range(1, 21):
        users.append({
            'user_id': i,
            'username': f'user_{i}',
            'favorite_genres': random.sample(['rock', 'pop', 'jazz', 'electronic', 'classical', 'hip-hop'], k=random.randint(1, 3)),
            'preferred_mood': random.choice(['happy', 'sad', 'energetic', 'calm', 'aggressive']),
            'listening_history': random.sample(range(1, 51), k=random.randint(5, 15))
        })
    return users

# Initialize datasets
df_songs = pd.DataFrame(create_music_dataset())
users = create_user_dataset()
df_users = pd.DataFrame(users)

# Feature engineering
def calculate_song_features(song_data):
    features = song_data[['tempo', 'energy', 'danceability', 'popularity']].values
    scaler = MinMaxScaler()
    return scaler.fit_transform(features)

# Content-based recommendation
def get_content_based_recommendations(song_id: int, n_recommendations: int = 5):
    features = calculate_song_features(df_songs)
    similarity = cosine_similarity(features)
    
    song_idx = df_songs[df_songs['song_id'] == song_id].index[0]
    similar_scores = list(enumerate(similarity[song_idx]))
    similar_scores = sorted(similar_scores, key=lambda x: x[1], reverse=True)
    
    recommendations = []
    for idx, score in similar_scores[1:n_recommendations+1]:
        song = df_songs.iloc[idx]
        recommendations.append({
            'song_id': int(song['song_id']),
            'title': song['title'],
            'artist': song['artist'],
            'genre': song['genre'],
            'similarity_score': float(score)
        })
    return recommendations

# Collaborative filtering
def get_collaborative_recommendations(user_id: int, n_recommendations: int = 5):
    user = df_users[df_users['user_id'] == user_id].iloc[0]
    user_history = set(user['listening_history'])
    favorite_genres = set(user['favorite_genres'])
    
    # Find similar users based on genre preferences
    similar_users = df_users[df_users['user_id'] != user_id].apply(
        lambda x: len(set(x['favorite_genres']) & favorite_genres) / len(favorite_genres),
        axis=1
    )
    
    # Get recommendations from similar users' history
    recommendations = []
    for similar_user_id in similar_users.nlargest(3).index:
        similar_user = df_users.iloc[similar_user_id]
        recommendations.extend([
            song_id for song_id in similar_user['listening_history']
            if song_id not in user_history
        ])
    
    # Get unique recommendations and sort by popularity
    recommendations = list(set(recommendations))
    recommended_songs = df_songs[df_songs['song_id'].isin(recommendations)]
    recommended_songs = recommended_songs.nlargest(n_recommendations, 'popularity')
    
    return recommended_songs.to_dict('records')

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Hybrid Music Recommendation System API"}

@app.get("/recommendations/content/{song_id}")
def content_recommendations(song_id: int, n_recommendations: int = 5):
    if song_id not in df_songs['song_id'].values:
        raise HTTPException(status_code=404, detail="Song not found")
    return get_content_based_recommendations(song_id, n_recommendations)

@app.get("/recommendations/collaborative/{user_id}")
def collaborative_recommendations(user_id: int, n_recommendations: int = 5):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    return get_collaborative_recommendations(user_id, n_recommendations)

@app.get("/recommendations/hybrid/{user_id}")
def hybrid_recommendations(user_id: int, n_recommendations: int = 5):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Combine both recommendation types
    collaborative_recs = get_collaborative_recommendations(user_id, n_recommendations)
    content_recs = []
    
    # Get content-based recommendations for the user's most recent song
    user_history = df_users[df_users['user_id'] == user_id].iloc[0]['listening_history']
    if user_history:
        recent_song_id = user_history[-1]
        content_recs = get_content_based_recommendations(recent_song_id, n_recommendations)
    
    # Combine and deduplicate recommendations
    all_recs = collaborative_recs + content_recs
    seen_songs = set()
    unique_recs = []
    
    for rec in all_recs:
        if rec['song_id'] not in seen_songs:
            seen_songs.add(rec['song_id'])
            unique_recs.append(rec)
            if len(unique_recs) >= n_recommendations:
                break
    
    return unique_recs

@app.get("/users/{user_id}")
def get_user_profile(user_id: int):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    return df_users[df_users['user_id'] == user_id].iloc[0].to_dict()

@app.get("/songs/search")
def search_songs(
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None
):
    filtered_songs = df_songs.copy()
    
    if genre:
        filtered_songs = filtered_songs[filtered_songs['genre'] == genre]
    if mood:
        filtered_songs = filtered_songs[filtered_songs['mood'] == mood]
    if min_year:
        filtered_songs = filtered_songs[filtered_songs['release_year'] >= min_year]
    if max_year:
        filtered_songs = filtered_songs[filtered_songs['release_year'] <= max_year]
        
    return filtered_songs.to_dict('records')
