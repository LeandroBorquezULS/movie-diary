import requests
from backend.core.config import TMDB_API_KEY
from backend.database import cache_movie, cache_search, get_cached_movie, get_cached_search
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def _request(path: str, params: dict | None = None):
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY no está configurada")

    response = requests.get(
        f"{BASE_URL}{path}",
        params={"api_key": TMDB_API_KEY, "language": "es", **(params or {})},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _decorate_movie(movie: dict):
    poster_path = movie.get("poster_path")
    backdrop_path = movie.get("backdrop_path")
    movie["poster_url"] = f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None
    movie["backdrop_url"] = f"{IMAGE_BASE_URL}{backdrop_path}" if backdrop_path else None
    return movie


def search_movies(query: str):
    normalized_query = query.strip()
    cached = get_cached_search(normalized_query)
    if cached is not None:
        return cached

    results = _request("/search/movie", {"query": normalized_query})
    for movie in results.get("results", []):
        _decorate_movie(movie)
    cache_search(normalized_query, results)
    return results


def get_movie_details(movie_id: int):
    cached = get_cached_movie(movie_id)
    if cached is not None:
        return cached

    movie = _decorate_movie(_request(f"/movie/{movie_id}"))
    cache_movie(movie)
    return movie


def get_recommendations(movie_id: int):
    recommendations = _request(f"/movie/{movie_id}/recommendations")
    for movie in recommendations.get("results", []):
        _decorate_movie(movie)
    return recommendations


def discover_movies_by_genres(genre_ids: list[int], page: int = 1):
    if not genre_ids:
        return {"results": []}

    results = _request(
        "/discover/movie",
        {
            "with_genres": ",".join(str(genre_id) for genre_id in genre_ids),
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
            "page": page,
        },
    )
    for movie in results.get("results", []):
        _decorate_movie(movie)
    return results


def get_genres():
    payload = _request("/genre/movie/list")
    return payload.get("genres", [])
