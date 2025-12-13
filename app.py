# app.py
import pickle
import pandas as pd
import requests
import streamlit as st
from urllib.parse import quote_plus
import os

# --- Load data ---
# --- Load data from GitHub Releases ---
MOVIE_DICT_URL = "https://github.com/nenusudharshan/movie-recommender/releases/download/v1.0/movie_dict.pkl"
MOVIES_URL = "https://github.com/nenusudharshan/movie-recommender/releases/download/v1.0/movies.pkl"
SIMILARITY_URL = "https://github.com/nenusudharshan/movie-recommender/releases/download/v1.0/similarity.pkl"

@st.cache_data(show_spinner=True)
def load_pickle(url):
    response = requests.get(url)
    return pickle.loads(response.content)

movies_dict = load_pickle(MOVIE_DICT_URL)
movies = pd.DataFrame(movies_dict)

movies_list = load_pickle(MOVIES_URL)
similarity = load_pickle(SIMILARITY_URL)



# --- Secrets / API key ---
OMDB_API_KEY = st.secrets.get("OMDB_KEY")

# --- Helper: fetch poster (cached) ---
@st.cache_data(ttl=60*60*24)  # cache for one day
def fetch_poster(title):
    """
    Fetch poster URL from OMDb using movie title.
    Uses URL encoding and returns None if not found.
    """
    if not OMDB_API_KEY:
        return None

    q = quote_plus(title)
    url = f"http://www.omdbapi.com/?t={q}&apikey={OMDB_API_KEY}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    if data.get("Response") == "True" and data.get("Poster") and data.get("Poster") != "N/A":
        return data["Poster"]
    return None

# --- Recommender (returns titles list) ---
def recommend(movie_title, top_n=5):
    try:
        idx = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        return []
    distances = similarity[idx]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1: top_n+1]
    return [movies.iloc[i[0]]['title'] for i in movies_list]

# --- Streamlit UI ---
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender System")
st.markdown("### Find similar movies instantly based on your taste 🍿")
st.write("")  # small spacing

selected_movie_name = st.selectbox(
    "🎬 Select a movie to get recommendations:",
    movies['title'].values
)

top_n = st.slider("Number of recommendations", 3, 10, 5)

# --- inside your if st.button('Recommend'): block, replace the display part with this ---
if st.button('Recommend'):
    recommendations = recommend(selected_movie_name, top_n=top_n)

    if not recommendations:
        st.warning("No recommendations found for this movie.")
    else:
        st.markdown("## Recommended Movies ⭐")
        n_cols = min(3, top_n)
        cols = st.columns(n_cols)

        for index, movie in enumerate(recommendations):
            poster_url = fetch_poster(movie)
            col = cols[index % n_cols]

            with col:
                st.markdown(f"**{movie}**")
                if poster_url:
                    st.image(poster_url, width=200)
                else:
                    st.write("Poster not available")

st.markdown("""
---
Made with ❤️ using Streamlit  
""")


