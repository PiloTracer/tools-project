"""Encrypt / decrypt GitHub PATs at rest (Fernet). Key from env or derived from JWT_SECRET."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet_key() -> bytes:
    raw = os.environ.get("GITHUB_TOKEN_ENCRYPTION_KEY", "").strip()
    if raw:
        if len(raw) == 44 and raw.endswith("="):
            return raw.encode()
        digest = hashlib.sha256(raw.encode()).digest()
        return base64.urlsafe_b64encode(digest)
    digest = hashlib.sha256(get_settings().jwt_secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_github_token(plaintext: str) -> str:
    f = Fernet(_fernet_key())
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_github_token(cipher_b64: str) -> str:
    f = Fernet(_fernet_key())
    try:
        return f.decrypt(cipher_b64.encode("ascii")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Could not decrypt stored GitHub token (wrong key?)") from e
