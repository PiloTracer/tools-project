"""Tests for GitHub PAT encryption helpers.

!!! NEVER put real keys or secrets in test files — they WILL leak into git history !!!
Use obviously-fake test-only values that cannot be mistaken for production secrets.
Every key below is synthetically constructed or clearly nonsensical.
"""

from __future__ import annotations

import os

import pytest

from app.services.github_token_crypto import decrypt_github_token, encrypt_github_token

# Synthetic test-only Fernet key — 'g' ensures version byte 0x80, remaining chars
# are obvious 'A' filler. This is NEVER a real key.
_TEST_FERNET_KEY_44 = "gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

# Test-only key for the SHA-256 derived path (deliberately not 44 chars).
_TEST_DERIVED_KEY = "test-fernet-key-32-bytes-ok!!!"


def test_roundtrip_fernet_direct() -> None:
    """Direct Fernet path: exactly 44 chars ending with '='."""
    os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = _TEST_FERNET_KEY_44
    plaintext = "ghp_super_secret_token"
    cipher = encrypt_github_token(plaintext)
    assert cipher != plaintext
    assert decrypt_github_token(cipher) == plaintext


def test_roundtrip_derived() -> None:
    """SHA-256 derived key path: raw value is not a 44-char b64 key."""
    os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = _TEST_DERIVED_KEY
    plaintext = "ghp_another_token"
    cipher = encrypt_github_token(plaintext)
    assert decrypt_github_token(cipher) == plaintext


def test_missing_key_raises() -> None:
    os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = ""
    with pytest.raises(RuntimeError):
        encrypt_github_token("token")
