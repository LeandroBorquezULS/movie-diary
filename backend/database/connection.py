from psycopg import connect
from psycopg.rows import dict_row

from backend.core.config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada")
    return connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS accounts")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS catalog")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts.users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TIMESTAMPTZ NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts.sessions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES accounts.users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts.favorite_genres (
                    user_id BIGINT NOT NULL REFERENCES accounts.users(id) ON DELETE CASCADE,
                    genre_id INTEGER NOT NULL,
                    genre_name TEXT NOT NULL,
                    PRIMARY KEY (user_id, genre_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog.movies_cache (
                    id BIGINT PRIMARY KEY,
                    title TEXT NOT NULL,
                    original_title TEXT,
                    overview TEXT,
                    release_date TEXT,
                    poster_path TEXT,
                    backdrop_path TEXT,
                    vote_average DOUBLE PRECISION,
                    runtime INTEGER,
                    genres_json JSONB NOT NULL,
                    details_json JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog.search_cache (
                    query TEXT PRIMARY KEY,
                    results_json JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog.movie_views (
                    user_id BIGINT NOT NULL REFERENCES accounts.users(id) ON DELETE CASCADE,
                    movie_id BIGINT NOT NULL REFERENCES catalog.movies_cache(id) ON DELETE CASCADE,
                    viewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, movie_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS catalog.movie_feedback (
                    user_id BIGINT NOT NULL REFERENCES accounts.users(id) ON DELETE CASCADE,
                    movie_id BIGINT NOT NULL REFERENCES catalog.movies_cache(id) ON DELETE CASCADE,
                    recommended BOOLEAN NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, movie_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_movie_views_movie_id
                ON catalog.movie_views (movie_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_movie_feedback_movie_id
                ON catalog.movie_feedback (movie_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_token_hash
                ON accounts.sessions (token_hash)
                """
            )
