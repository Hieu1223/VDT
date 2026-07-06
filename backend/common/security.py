"""Password hashing and JWT helpers. Pure utilities - no FastAPI/DB imports here."""
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Literal

from common.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _create_token(sub: str, token_type: Literal["access", "refresh"], ttl: timedelta, extra: dict | None = None) -> str:
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + ttl,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str, username: str) -> str:
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.jwt_access_ttl_minutes),
        {"role": role, "username": username},
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.jwt_refresh_ttl_days))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
