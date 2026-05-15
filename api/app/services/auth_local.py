from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import Settings, get_settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def create_local_access_token(
    *,
    user_id: str,
    email: str,
    is_superuser: bool,
    settings: Settings | None = None,
) -> tuple[str, int]:
    settings = settings or get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    exp_seconds = int(settings.access_token_expire_minutes * 60)
    payload = {
        "sub": user_id,
        "email": email,
        "superuser": is_superuser,
        "token_typ": "local",
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return token, exp_seconds


def decode_local_token(token: str, settings: Settings | None = None) -> dict | None:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("token_typ") != "local":
            return None
        return payload
    except JWTError:
        return None
