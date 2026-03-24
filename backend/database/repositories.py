import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from psycopg.errors import UniqueViolation

from backend.core.config import LOCKOUT_MINUTES, MAX_LOGIN_ATTEMPTS
from backend.core.security import hash_token
from backend.database.connection import get_connection


def row_to_movie(row: dict | None):
    if row is None:
        return None
    movie = row["details_json"]
    movie["genres"] = row["genres_json"]
    return movie


def cache_movie(movie: dict):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.movies_cache (
                    id, title, original_title, overview, release_date, poster_path,
                    backdrop_path, vote_average, runtime, genres_json, details_json, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    original_title = EXCLUDED.original_title,
                    overview = EXCLUDED.overview,
                    release_date = EXCLUDED.release_date,
                    poster_path = EXCLUDED.poster_path,
                    backdrop_path = EXCLUDED.backdrop_path,
                    vote_average = EXCLUDED.vote_average,
                    runtime = EXCLUDED.runtime,
                    genres_json = EXCLUDED.genres_json,
                    details_json = EXCLUDED.details_json,
                    updated_at = NOW()
                """,
                (
                    movie["id"],
                    movie.get("title") or "",
                    movie.get("original_title"),
                    movie.get("overview"),
                    movie.get("release_date"),
                    movie.get("poster_path"),
                    movie.get("backdrop_path"),
                    movie.get("vote_average"),
                    movie.get("runtime"),
                    json.dumps(movie.get("genres", []), ensure_ascii=False),
                    json.dumps(movie, ensure_ascii=False),
                ),
            )


def get_cached_movie(movie_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT genres_json, details_json FROM catalog.movies_cache WHERE id = %s",
                (movie_id,),
            )
            row = cursor.fetchone()
    return row_to_movie(row)


def cache_search(query: str, results: dict):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.search_cache (query, results_json, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (query) DO UPDATE SET
                    results_json = EXCLUDED.results_json,
                    updated_at = NOW()
                """,
                (query.lower().strip(), json.dumps(results, ensure_ascii=False)),
            )


def get_cached_search(query: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT results_json FROM catalog.search_cache WHERE query = %s",
                (query.lower().strip(),),
            )
            row = cursor.fetchone()
    return None if row is None else row["results_json"]


def create_user(username: str, password_hash: str, password_salt: str):
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO accounts.users (username, password_hash, password_salt)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (username.strip(), password_hash, password_salt),
                )
                return cursor.fetchone()["id"]
    except UniqueViolation:
        raise


def list_users():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, created_at, updated_at
                FROM accounts.users
                ORDER BY username
                """
            )
            return cursor.fetchall()


def get_user(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, created_at, updated_at
                FROM accounts.users
                WHERE id = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()


def get_user_auth(username: str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password_hash, password_salt,
                       failed_login_attempts, locked_until, created_at, updated_at
                FROM accounts.users
                WHERE LOWER(username) = LOWER(%s)
                """,
                (username.strip(),),
            )
            return cursor.fetchone()


def register_failed_login_attempt(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE accounts.users
                SET
                    failed_login_attempts = failed_login_attempts + 1,
                    locked_until = CASE
                        WHEN failed_login_attempts + 1 >= %s THEN NOW() + (%s * INTERVAL '1 minute')
                        ELSE locked_until
                    END,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, user_id),
            )


def reset_failed_login_attempts(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE accounts.users
                SET failed_login_attempts = 0, locked_until = NULL, updated_at = NOW()
                WHERE id = %s
                """,
                (user_id,),
            )


def create_user_session(user_id: int, token: str, duration_days: int = 14):
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO accounts.sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (user_id, token_hash, expires_at),
            )
            return cursor.fetchone()["id"]


def get_user_by_session_token(token: str):
    token_hash = hash_token(token)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.username, u.created_at, u.updated_at
                FROM accounts.sessions s
                JOIN accounts.users u ON u.id = s.user_id
                WHERE s.token_hash = %s AND s.expires_at > NOW()
                """,
                (token_hash,),
            )
            return cursor.fetchone()


def delete_user_session(token: str):
    token_hash = hash_token(token)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM accounts.sessions WHERE token_hash = %s",
                (token_hash,),
            )


def update_user_credentials(
    user_id: int,
    username: str | None = None,
    password_hash: str | None = None,
    password_salt: str | None = None,
):
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT username, password_hash, password_salt
                    FROM accounts.users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                user = cursor.fetchone()
                if user is None:
                    return False

                cursor.execute(
                    """
                    UPDATE accounts.users
                    SET username = %s, password_hash = %s, password_salt = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        username if username is not None else user["username"],
                        password_hash if password_hash is not None else user["password_hash"],
                        password_salt if password_salt is not None else user["password_salt"],
                        user_id,
                    ),
                )
                return True
    except UniqueViolation:
        raise


def delete_user(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM accounts.users WHERE id = %s", (user_id,))


def replace_favorite_genres(user_id: int, genres):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM accounts.favorite_genres WHERE user_id = %s", (user_id,))
            for genre in genres:
                cursor.execute(
                    """
                    INSERT INTO accounts.favorite_genres (user_id, genre_id, genre_name)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, genre["id"], genre["name"]),
                )


def get_favorite_genres(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT genre_id AS id, genre_name AS name
                FROM accounts.favorite_genres
                WHERE user_id = %s
                ORDER BY genre_name
                """,
                (user_id,),
            )
            return cursor.fetchall()


def mark_movie_viewed(user_id: int, movie_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.movie_views (user_id, movie_id, viewed_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (user_id, movie_id) DO UPDATE SET viewed_at = NOW()
                """,
                (user_id, movie_id),
            )


def set_movie_feedback(user_id: int, movie_id: int, recommended: bool):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO catalog.movie_feedback (user_id, movie_id, recommended, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, movie_id) DO UPDATE SET
                    recommended = EXCLUDED.recommended,
                    updated_at = NOW()
                """,
                (user_id, movie_id, recommended),
            )


def get_movie_feedback(user_id: int, movie_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recommended
                FROM catalog.movie_feedback
                WHERE user_id = %s AND movie_id = %s
                """,
                (user_id, movie_id),
            )
            row = cursor.fetchone()
    return None if row is None else row["recommended"]


def get_user_recent_movies(user_id: int, limit: int = 5):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT m.details_json, m.genres_json
                FROM catalog.movie_views v
                JOIN catalog.movies_cache m ON m.id = v.movie_id
                WHERE v.user_id = %s
                ORDER BY v.viewed_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
    return [row_to_movie(row) for row in rows]


def get_user_history(user_id: int):
    grouped = defaultdict(list)
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    v.viewed_at,
                    m.details_json,
                    COALESCE(f.recommended, NULL) AS recommended
                FROM catalog.movie_views v
                JOIN catalog.movies_cache m ON m.id = v.movie_id
                LEFT JOIN catalog.movie_feedback f
                    ON f.user_id = v.user_id AND f.movie_id = v.movie_id
                WHERE v.user_id = %s
                ORDER BY v.viewed_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

    for row in rows:
        viewed_at = row["viewed_at"]
        key = viewed_at.strftime("%Y-%m")
        grouped[key].append(
            {
                "viewed_at": viewed_at.isoformat(),
                "recommended": row["recommended"],
                "movie": row["details_json"],
            }
        )

    return [{"period": period, "entries": entries} for period, entries in grouped.items()]


def get_user_viewed_movie_ids(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT movie_id FROM catalog.movie_views WHERE user_id = %s",
                (user_id,),
            )
            rows = cursor.fetchall()
    return {row["movie_id"] for row in rows}


def get_user_blocked_movie_ids(user_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT movie_id
                FROM catalog.movie_feedback
                WHERE user_id = %s AND recommended = FALSE
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
    return {row["movie_id"] for row in rows}


def get_movie_community_stats(movie_id: int):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE((SELECT COUNT(*) FROM catalog.movie_views WHERE movie_id = %s), 0) AS viewed_count,
                    COALESCE((SELECT COUNT(*) FROM catalog.movie_feedback WHERE movie_id = %s AND recommended = TRUE), 0) AS recommend_count,
                    COALESCE((SELECT COUNT(*) FROM catalog.movie_feedback WHERE movie_id = %s AND recommended = FALSE), 0) AS not_recommend_count
                """,
                (movie_id, movie_id, movie_id),
            )
            return cursor.fetchone()
