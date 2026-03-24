import hashlib
import hmac
import secrets
import re

from backend.core.config import ENFORCE_STRONG_PASSWORDS

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None):
    salt = salt or secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return {"salt": salt, "hash": password_hash}


def verify_password(password: str, password_hash: str, salt: str):
    candidate = hash_password(password, salt)["hash"]
    return hmac.compare_digest(candidate, password_hash)


def generate_session_token():
    return secrets.token_urlsafe(48)


def hash_token(token: str):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_password_policy(password: str):
    if not ENFORCE_STRONG_PASSWORDS:
        return True, None
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    if len(password) < 8 or not (has_upper and has_lower and has_digit):
        return False, "La contraseña no cumple la política configurada"
    return True, None
