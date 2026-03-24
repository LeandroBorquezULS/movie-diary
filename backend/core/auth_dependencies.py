from fastapi import Header, HTTPException

from backend.database import get_user_by_session_token


def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesión no válida")

    token = authorization.removeprefix("Bearer ").strip()
    user = get_user_by_session_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return user


def get_optional_current_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()
    return get_user_by_session_token(token)
