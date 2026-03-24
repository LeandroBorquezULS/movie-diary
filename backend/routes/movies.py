from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import IntegrityError

from backend.core.auth_dependencies import get_current_user, get_optional_current_user
from backend.core.security import (
    generate_session_token,
    hash_password,
    validate_password_policy,
    verify_password,
)
from backend.database import (
    cache_movie,
    create_user_session,
    create_user,
    delete_user,
    delete_user_session,
    get_favorite_genres,
    get_movie_community_stats,
    get_movie_feedback,
    get_user,
    get_user_auth,
    get_user_blocked_movie_ids,
    get_user_history,
    get_user_recent_movies,
    get_user_viewed_movie_ids,
    mark_movie_viewed,
    register_failed_login_attempt,
    reset_failed_login_attempts,
    replace_favorite_genres,
    set_movie_feedback,
    update_user_credentials,
)
from backend.models.schemas import (
    AccountUpdatePayload,
    DeleteAccountPayload,
    FavoriteGenresPayload,
    LoginPayload,
    MovieActionPayload,
    RegisterPayload,
)
from backend.services.recommendation_engine import compute_ranked_candidates
from backend.services.tmdb_service import (
    discover_movies_by_genres,
    get_genres,
    get_movie_details,
    get_recommendations,
    search_movies,
)


router = APIRouter()


def _genres_map():
    return {genre["id"]: genre for genre in get_genres()}


def _public_user(user_id: int):
    user = get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user["favorite_genres"] = get_favorite_genres(user_id)
    return user


def _movie_card(movie: dict, reason: str | None = None, source_score: int = 0):
    community_stats = get_movie_community_stats(movie["id"])
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "release_date": movie.get("release_date"),
        "vote_average": movie.get("vote_average"),
        "poster_url": movie.get("poster_url"),
        "backdrop_url": movie.get("backdrop_url"),
        "genre_ids": movie.get("genre_ids") or [genre["id"] for genre in movie.get("genres", [])],
        "reason": reason,
        "source_score": source_score,
        "community_stats": community_stats,
    }


def _build_ranked_list(
    candidates: list[dict],
    genre_weights: dict[int, int],
    favorite_genre_ids: set[int],
    blocked_ids: set[int],
    viewed_ids: set[int],
    limit: int,
):
    deduped: dict[int, dict] = {}
    for candidate in candidates:
        movie_id = candidate["id"]
        if movie_id in blocked_ids or movie_id in viewed_ids:
            continue
        current = deduped.get(movie_id)
        if current is None or candidate.get("source_score", 0) > current.get("source_score", 0):
            deduped[movie_id] = candidate

    ranked = compute_ranked_candidates(list(deduped.values()), genre_weights, favorite_genre_ids)
    return ranked[:limit]


@router.get("/genres")
def genres():
    return {"genres": get_genres()}


@router.post("/auth/register")
def register(payload: RegisterPayload):
    genres_map = _genres_map()
    selected_genres = [genres_map[genre_id] for genre_id in payload.favorite_genre_ids if genre_id in genres_map]
    is_valid_password, password_error = validate_password_policy(payload.password)
    if not is_valid_password:
        raise HTTPException(status_code=400, detail=password_error)
    password_data = hash_password(payload.password)

    try:
        user_id = create_user(payload.username, password_data["hash"], password_data["salt"])
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Ese usuario ya existe") from exc

    replace_favorite_genres(user_id, selected_genres)
    token = generate_session_token()
    create_user_session(user_id, token)
    return {"user": _public_user(user_id), "token": token}


@router.post("/auth/login")
def login(payload: LoginPayload):
    user = get_user_auth(payload.username)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")

    if user.get("locked_until") and user["locked_until"] > datetime.now(timezone.utc):
        raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente por intentos fallidos")

    if not user.get("password_hash") or not verify_password(
        payload.password,
        user["password_hash"],
        user["password_salt"],
    ):
        register_failed_login_attempt(user["id"])
        raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")

    reset_failed_login_attempts(user["id"])
    token = generate_session_token()
    create_user_session(user["id"], token)
    return {"user": _public_user(user["id"]), "token": token}


@router.get("/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)):
    return {"user": _public_user(current_user["id"])}


@router.post("/auth/logout")
def logout(
    authorization: str | None = Header(default=None),
    current_user: dict = Depends(get_current_user),
):
    if authorization and authorization.startswith("Bearer "):
        delete_user_session(authorization.removeprefix("Bearer ").strip())
    return {"status": "ok", "user_id": current_user["id"]}


@router.get("/users/me/profile")
def user_profile(current_user: dict = Depends(get_current_user)):
    return {"user": _public_user(current_user["id"])}


@router.get("/users/me/history")
def user_history(current_user: dict = Depends(get_current_user)):
    return {
        "user": _public_user(current_user["id"]),
        "history": get_user_history(current_user["id"]),
    }


@router.put("/users/me/account")
def update_account(payload: AccountUpdatePayload, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    auth_user = get_user_auth(_public_user(user_id)["username"])
    if auth_user is None or not verify_password(
        payload.current_password,
        auth_user["password_hash"],
        auth_user["password_salt"],
    ):
        raise HTTPException(status_code=401, detail="Contraseña actual inválida")

    next_username = payload.new_username.strip() if payload.new_username else None
    password_hash = None
    password_salt = None
    if payload.new_password:
        is_valid_password, password_error = validate_password_policy(payload.new_password)
        if not is_valid_password:
            raise HTTPException(status_code=400, detail=password_error)
        password_data = hash_password(payload.new_password)
        password_hash = password_data["hash"]
        password_salt = password_data["salt"]

    try:
        updated = update_user_credentials(
            user_id,
            username=next_username,
            password_hash=password_hash,
            password_salt=password_salt,
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Ese usuario ya existe") from exc

    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"user": _public_user(user_id)}


@router.put("/users/me/favorite-genres")
def update_favorite_genres(payload: FavoriteGenresPayload, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    _public_user(user_id)
    genres_map = _genres_map()
    selected_genres = [genres_map[genre_id] for genre_id in payload.genre_ids if genre_id in genres_map]
    replace_favorite_genres(user_id, selected_genres)
    return {"favorite_genres": selected_genres}


@router.delete("/users/me")
def remove_account(payload: DeleteAccountPayload, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    auth_user = get_user_auth(_public_user(user_id)["username"])
    if auth_user is None or not verify_password(
        payload.password,
        auth_user["password_hash"],
        auth_user["password_salt"],
    ):
        raise HTTPException(status_code=401, detail="Contraseña inválida")
    delete_user(user_id)
    return {"status": "deleted"}


@router.get("/users/me/recommendations")
def personalized_recommendations(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    _public_user(user_id)
    recent_movies = get_user_recent_movies(user_id, limit=6)
    favorite_genres = get_favorite_genres(user_id)
    viewed_ids = get_user_viewed_movie_ids(user_id)
    blocked_ids = get_user_blocked_movie_ids(user_id)

    genre_weights = Counter()
    for index, movie in enumerate(recent_movies):
        recency_weight = max(1, 6 - index)
        for genre in movie.get("genres", []):
            genre_weights[genre["id"]] += recency_weight

    for genre in favorite_genres:
        genre_weights[genre["id"]] += 3

    candidates = []
    for movie in recent_movies[:3]:
        related_movies = get_recommendations(movie["id"]).get("results", [])[:10]
        for related in related_movies:
            candidates.append(
                _movie_card(
                    related,
                    reason=f"Porque viste {movie['title']}",
                    source_score=14,
                )
            )

    top_genres = [genre_id for genre_id, _ in genre_weights.most_common(3)]
    for discovered in discover_movies_by_genres(top_genres).get("results", [])[:18]:
        candidates.append(
            _movie_card(
                discovered,
                reason="Coincide con tus géneros favoritos",
                source_score=8,
            )
        )

    ranked = _build_ranked_list(
        candidates,
        genre_weights=dict(genre_weights),
        favorite_genre_ids={genre["id"] for genre in favorite_genres},
        blocked_ids=blocked_ids,
        viewed_ids=viewed_ids,
        limit=12,
    )

    return {
        "user": _public_user(user_id),
        "recent_movies": [_movie_card(movie) for movie in recent_movies],
        "algorithm": {
            "name": "Stable Merge Sort Ranking",
            "summary": (
                "La puntuación combina comunidad local, afinidad por géneros y origen de la sugerencia. "
                "Luego se ordena con merge sort para mantener estabilidad y costo O(n log n)."
            ),
            "weights": {
                "source_related_recent_movie": 14,
                "source_favorite_genres": 8,
                "community_recommend": 6,
                "community_not_recommend": -4,
                "community_view": 2,
                "favorite_genre_bonus": 2,
            },
        },
        "results": ranked,
    }


@router.get("/search")
def search(query: str):
    return search_movies(query)


@router.get("/{movie_id}")
def movie_details(movie_id: int, current_user: dict | None = Depends(get_optional_current_user)):
    movie = get_movie_details(movie_id)
    response = {
        **movie,
        "cached": True,
        "community_stats": get_movie_community_stats(movie_id),
    }
    if current_user is not None:
        user_id = current_user["id"]
        response["user_feedback"] = get_movie_feedback(user_id, movie_id)
        response["viewed"] = movie_id in get_user_viewed_movie_ids(user_id)
    return response


@router.post("/views")
def register_view(payload: MovieActionPayload, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    movie = get_movie_details(payload.movie_id)
    cache_movie(movie)
    mark_movie_viewed(user_id, payload.movie_id)
    return {"status": "ok", "movie_id": payload.movie_id}


@router.post("/feedback")
def register_feedback(payload: MovieActionPayload, current_user: dict = Depends(get_current_user)):
    if payload.recommended is None:
        raise HTTPException(status_code=400, detail="Debe indicar recommended")
    user_id = current_user["id"]
    movie = get_movie_details(payload.movie_id)
    cache_movie(movie)
    set_movie_feedback(user_id, payload.movie_id, payload.recommended)
    return {"status": "ok", "movie_id": payload.movie_id, "recommended": payload.recommended}


@router.get("/{movie_id}/recommendations")
def recommendations(movie_id: int, current_user: dict | None = Depends(get_optional_current_user)):
    movie = get_movie_details(movie_id)
    payload = get_recommendations(movie_id)
    favorites = set()
    blocked_ids = set()
    viewed_ids = set()
    genre_weights = Counter()

    if current_user is not None:
        user_id = current_user["id"]
        favorites = {genre["id"] for genre in get_favorite_genres(user_id)}
        blocked_ids = get_user_blocked_movie_ids(user_id)
        viewed_ids = get_user_viewed_movie_ids(user_id)
        for genre in get_user_recent_movies(user_id, limit=5):
            for item in genre.get("genres", []):
                genre_weights[item["id"]] += 2

    candidates = [
        _movie_card(related, reason=f"Relacionada con {movie['title']}", source_score=12)
        for related in payload.get("results", [])
    ]

    ranked = _build_ranked_list(
        candidates,
        genre_weights=dict(genre_weights),
        favorite_genre_ids=favorites,
        blocked_ids=blocked_ids,
        viewed_ids=viewed_ids,
        limit=12,
    )

    return {
        "movie": _movie_card(movie),
        "results": ranked,
    }
