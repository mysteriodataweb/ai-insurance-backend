from uuid import uuid4

import jwt

from app.config import settings
from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery")
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password("correct horse battery", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("anything", "garbage")
    assert hash_password("same") != hash_password("same")


def test_token_roundtrip_and_tampering():
    user_id = uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id
    assert decode_access_token(token + "x") is None
    forged = jwt.encode({"sub": str(user_id)}, "another-secret", algorithm="HS256")
    assert decode_access_token(forged) is None


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    assert decode_access_token(create_access_token(uuid4())) is None
