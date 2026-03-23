import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

url = "https://api.themoviedb.org/3/search/movie"
params = {
    "api_key": API_KEY,
    "query": "batman"
}

response = requests.get(url, params=params)

print(response.status_code)
print(response.json())