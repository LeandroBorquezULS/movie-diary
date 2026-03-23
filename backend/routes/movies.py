from fastapi import APIRouter
from services.tmdb_service import (
    search_movies,
    get_movie_details,
    get_recommendations
)

router = APIRouter()


@router.get("/search")
def search(query: str):
    return search_movies(query)


@router.get("/{movie_id}")
def movie_details(movie_id: int):
    return get_movie_details(movie_id)


@router.get("/{movie_id}/recommendations")
def recommendations(movie_id: int):
    return get_recommendations(movie_id)