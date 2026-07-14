import jwt
import pytest

from app.core import security


def test_password_roundtrip():
    h = security.hash_password("secret123")
    assert h != "secret123"
    assert security.verify_password("secret123", h) is True
    assert security.verify_password("wrong", h) is False


def test_access_token_carries_role():
    tok = security.create_access_token(sub="user-1", role="admin")
    payload = security.decode_token(tok)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_decode_rejects_garbage():
    with pytest.raises(jwt.PyJWTError):
        security.decode_token("not-a-token")
