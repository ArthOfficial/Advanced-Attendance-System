import hashlib
import hmac
import json

from app.config import settings


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def sign_payload(payload: dict) -> str:
    return hmac.new(settings.jwt_secret.encode(), _canon(payload), hashlib.sha256).hexdigest()


def verify_payload(payload: dict, sig: str) -> bool:
    return hmac.compare_digest(sign_payload(payload), sig)
