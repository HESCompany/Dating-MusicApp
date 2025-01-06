from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import TruncatedSVD
import random
from collections import Counter
from keras import layers, Model

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


df_songs = pd.read_csv('dsapp\dataset.csv')
df_songs['song_id'] = range(1, len(df_songs) + 1)  


def create_user_dataset():
    users = []
    for i in range(1, 21):
        users.append({
            'user_id': i,
            'username': f'user_{i}',
            'favorite_genres': random.sample(df_songs['track_genre'].unique().tolist(), k=random.randint(1, 3)),
            'listening_history': random.sample(df_songs['song_id'].tolist(), k=random.randint(5, 15))
        })
    return users

df_users = pd.DataFrame(create_user_dataset())

def create_user_profile(user_id):
    user = df_users[df_users['user_id'] == user_id].iloc[0]
    user_history = user['listening_history']
    user_songs = df_songs[df_songs['song_id'].isin(user_history)]
    
    profile = {
        'energy': user_songs['energy'].mean(),
        'danceability': user_songs['danceability'].mean(),
        'tempo': user_songs['tempo'].mean() / max(df_songs['tempo']),
        'popularity': user_songs['popularity'].mean() / 100.0
    }
    
    genre_counts = Counter(user_songs['track_genre'])
    total_listens = sum(genre_counts.values())
    genre_prefs = {genre: count / total_listens for genre, count in genre_counts.items()}
    
    return profile, genre_prefs

def get_recommendations(user_id: int, n_recommendations: int = 5):
    user_profile, user_genre_prefs = create_user_profile(user_id)
    
    
    scaler = MinMaxScaler()
    features = df_songs[['energy', 'danceability', 'tempo', 'popularity']].values
    songs_scaled = scaler.fit_transform(features)
    
    user_vector = np.array([
        user_profile['energy'],
        user_profile['danceability'],
        user_profile['tempo'],
        user_profile['popularity']
    ]).reshape(1, -1)
    user_scaled = scaler.transform(user_vector)
    
    
    similarities = cosine_similarity(user_scaled, songs_scaled)[0]
    
    
    genre_weights = [user_genre_prefs.get(genre, 0) for genre in df_songs['track_genre']]
    weighted_similarities = similarities + np.array(genre_weights)
    
    
    top_indices = weighted_similarities.argsort()[-n_recommendations:][::-1]
    recommendations = []
    
    for idx in top_indices:
        song = df_songs.iloc[idx]
        recommendations.append({
            'song_id': int(song['song_id']),
            'title': song['track_name'],
            'artist': song['artists'],
            'genre': song['track_genre'],
            'similarity_score': float(weighted_similarities[idx])
        })
    
    return recommendations

@app.get("/")
def read_root():
    return {"message": "Music Recommendation System API"}

@app.get("/recommendations/{user_id}")
def get_user_recommendations(user_id: int, n_recommendations: int = 5):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    return get_recommendations(user_id, n_recommendations)

@app.get("/users/{user_id}")
def get_user_profile(user_id: int):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    profile, genre_prefs = create_user_profile(user_id)
    user_data = df_users[df_users['user_id'] == user_id].iloc[0].to_dict()
    user_data['profile'] = profile
    user_data['genre_preferences'] = genre_prefs
    return user_data