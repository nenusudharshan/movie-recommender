# app.py
import pickle
import pandas as pd
import requests
import streamlit as st

# ========== LOAD PICKLE FILES FROM GITHUB RELEASE ==========
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

# ========== TMDB API (FROM STREAMLIT SECRETS) ==========
TMDB_KEY = st.secrets.get("TMDB_KEY")

# ========== FETCH POSTER FROM TMDB ==========
@st.cache_data(ttl=60*60*24)
def fetch_poster(movie_title):
    """
    Fetch high quality poster from TMDB using movie title.
    """
    if not TMDB_KEY:
        return None

    # Search movie by title
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={movie_title}"
    try:
        response = requests.get(search_url)
        data = response.json()
    except:
        return None

    # No movie found
    if "results" not in data or len(data["results"]) == 0:
        return None

    # Get poster path
    poster_path = data["results"][0].get("poster_path")
    if not poster_path:
        return None

    # Return full TMDB poster URL
    return f"https://image.tmdb.org/t/p/w500{poster_path}"

# ========== RECOMMENDER ==========
def recommend(movie_title, top_n=5):
    try:
        idx = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        return []

    distances = similarity[idx]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1: top_n+1]
    return [movies.iloc[i[0]]['title'] for i in movies_list]

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("🎬 Movie Recommender System")
st.markdown("### Find similar movies instantly based on your taste 🍿")

selected_movie_name = st.selectbox(
    "🎬 Select a movie to get recommendations:",
    movies['title'].values
)

top_n = st.slider("Number of recommendations", 3, 10, 5)

if st.button("Recommend"):
    recommendations = recommend(selected_movie_name, top_n=top_n)

    if not recommendations:
        st.warning("No recommendations found.")
    else:
        st.markdown("## ⭐ Recommended Movies")
        cols = st.columns(min(3, top_n))

        for index, title in enumerate(recommendations):
            poster_url = fetch_poster(title)
            col = cols[index % 3]

            with col:
                st.markdown(f"**{title}**")
                if poster_url:
                    st.image(poster_url, width=200)
                else:
                    st.write("Poster not available")

st.markdown("---")
st.write("Made with ❤️ using Streamlit")
