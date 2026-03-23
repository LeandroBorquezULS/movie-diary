import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def search_movies(query):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": API_KEY,
        "query": query,
        "language": "es"
    }
    return requests.get(url, params=params).json()


def get_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "es"
    }
    return requests.get(url, params=params).json()


def get_recommendations(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/recommendations"
    params = {
        "api_key": API_KEY,
        "language": "es"
    }
    return requests.get(url, params=params).json()