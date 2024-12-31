from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import TruncatedSVD
import random
from collections import Counter
import tensorflow as tf
from keras import layers, Model

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced dataset with audio features
def create_music_dataset():
    n_songs = 50
    return {
        'song_id': range(1, n_songs + 1),
        'title': [f'Song {i}' for i in range(1, n_songs + 1)],
        'artist': [f'Artist {i}' for i in range(1, n_songs + 1)],
        'mfcc': [np.random.rand(13) for _ in range(n_songs)],  # Simulated MFCC features
        'spectral': [np.random.rand(8) for _ in range(n_songs)],  # Simulated spectral features
        'tempo': np.random.randint(60, 180, n_songs),
        'energy': np.random.random(n_songs),
        'danceability': np.random.random(n_songs),
        'popularity': np.random.randint(0, 100, n_songs),
        'genre': np.random.choice(['rock', 'pop', 'jazz', 'electronic', 'classical', 'hip-hop'], n_songs),
    }

def create_user_dataset():
    users = []
    for i in range(1, 21):
        users.append({
            'user_id': i,
            'username': f'user_{i}',
            'favorite_genres': random.sample(['rock', 'pop', 'jazz', 'electronic', 'classical', 'hip-hop'], k=random.randint(1, 3)),
            'listening_history': random.sample(range(1, 51), k=random.randint(5, 15))
        })
    return users

# Initialize datasets
df_songs = pd.DataFrame(create_music_dataset())
users = create_user_dataset()
df_users = pd.DataFrame(users)

# Neural Collaborative Filtering Model
def create_ncf_model():
    n_users = len(df_users)
    n_songs = len(df_songs)
    n_factors = 50
    
    user_input = layers.Input(shape=(1,))
    song_input = layers.Input(shape=(1,))
    
    user_embedding = layers.Embedding(n_users + 1, n_factors)(user_input)
    song_embedding = layers.Embedding(n_songs + 1, n_factors)(song_input)
    
    user_vec = layers.Flatten()(user_embedding)
    song_vec = layers.Flatten()(song_embedding)
    
    concat = layers.Concatenate()([user_vec, song_vec])
    dense1 = layers.Dense(128, activation='relu')(concat)
    dense2 = layers.Dense(64, activation='relu')(dense1)
    output = layers.Dense(1, activation='sigmoid')(dense2)
    
    model = Model(inputs=[user_input, song_input], outputs=output)
    model.compile(optimizer='adam', loss='binary_crossentropy')
    return model

ncf_model = create_ncf_model()

def get_hybrid_recommendations(user_id: int, n_recommendations: int = 5):
    # Content-based features
    audio_features = np.array([np.concatenate([s, f]) for s, f in zip(df_songs['mfcc'], df_songs['spectral'])])
    content_similarity = cosine_similarity(audio_features)
    
    # Collaborative filtering with SVD
    user_history = df_users[df_users['user_id'] == user_id].iloc[0]['listening_history']
    # Change n_components to match number of songs
    svd = TruncatedSVD(n_components=min(len(df_songs), len(user_history)))
    user_item_matrix = pd.crosstab(pd.Series(range(1, len(df_users) + 1)), pd.Series(user_history))
    latent_features = svd.fit_transform(user_item_matrix)
    
    # Neural CF predictions
    user_ids = np.array([user_id] * len(df_songs))
    song_ids = np.array(df_songs['song_id'])
    ncf_predictions = ncf_model.predict([user_ids, song_ids])
    
    # Ensure all components have the same shape before combining
    content_scores = content_similarity.mean(axis=0)
    collab_scores = np.zeros(len(df_songs))
    collab_scores[:len(latent_features[user_id-1])] = latent_features[user_id-1]
    
    # Combine predictions with matching shapes
    final_scores = (0.4 * content_scores + 
                   0.3 * collab_scores + 
                   0.3 * ncf_predictions.flatten())
    
    # Get top recommendations
    top_indices = final_scores.argsort()[-n_recommendations:][::-1]
    recommendations = []
    
    for idx in top_indices:
        song = df_songs.iloc[idx]
        recommendations.append({
            'song_id': int(song['song_id']),
            'title': song['title'],
            'artist': song['artist'],
            'genre': song['genre'],
            'similarity_score': float(final_scores[idx])
        })
    
    return recommendations

@app.get("/")
def read_root():
    return {"message": "Hybrid Music Recommendation System API"}

@app.get("/recommendations/{user_id}")
def get_user_recommendations(user_id: int, n_recommendations: int = 5):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    return get_hybrid_recommendations(user_id, n_recommendations)

@app.get("/users/{user_id}")
def get_user_profile(user_id: int):
    if user_id not in df_users['user_id'].values:
        raise HTTPException(status_code=404, detail="User not found")
    user = df_users[df_users['user_id'] == user_id].iloc[0]
    user_history = user['listening_history']
    user_songs = df_songs[df_songs['song_id'].isin(user_history)]
    
    profile = {
        'energy': user_songs['energy'].mean(),
        'danceability': user_songs['danceability'].mean(),
        'tempo': user_songs['tempo'].mean() / 180.0,  # Normalize tempo to 0-1 range
        'popularity': user_songs['popularity'].mean() / 100.0  # Normalize popularity to 0-1 range
    }
    
    user_data = user.to_dict()
    user_data['profile'] = profile
    
    return user_data
