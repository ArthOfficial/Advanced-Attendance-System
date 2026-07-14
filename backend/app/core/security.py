from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_ph = PasswordHasher()


def hash_password(raw: str) -> str:
    return _ph.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, raw)
    except VerifyMismatchError:
        return False


def _encode(payload: dict, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_access_token(sub: str, role: str) -> str:
    return _encode({"sub": sub, "role": role, "type": "access"},
                   timedelta(minutes=settings.access_ttl_min))


def create_refresh_token(sub: str) -> str:
    return _encode({"sub": sub, "type": "refresh"},
                   timedelta(days=settings.refresh_ttl_days))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
