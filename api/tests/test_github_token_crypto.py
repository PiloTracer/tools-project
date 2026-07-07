"""Tests for GitHub PAT encryption helpers.

Keys are loaded from .env.dev (development) or .env (other environments).
Never hardcode real secrets in source — they WILL leak into git history.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.services.github_token_crypto import decrypt_github_token, encrypt_github_token


def _load_env_file(path: str) -> None:
    """Load KEY=VALUE pairs from an env file (no dotenv dependency).

    Only sets keys that aren't already in the environment, so explicitly-set
    values (Docker, CI) always take priority over file contents.
    """
    env_path = Path(__file__).resolve().parent.parent.parent / path
    if not env_path.is_file():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


# Load the appropriate env file so GITHUB_TOKEN_ENCRYPTION_KEY is available.
# In Docker, these files aren't mounted — but docker-compose already injects
# the vars, so the "already in environment" guard handles that case.
_load_env_file(".env.dev")
_load_env_file(".env")


def test_roundtrip_with_configured_key() -> None:
    """Encrypt/decrypt roundtrip using the configured GITHUB_TOKEN_ENCRYPTION_KEY."""
    key = os.environ.get("GITHUB_TOKEN_ENCRYPTION_KEY", "").strip()
    if not key:
        pytest.skip("GITHUB_TOKEN_ENCRYPTION_KEY not set in .env.dev, .env, or environment")
    plaintext = "ghp_test_token_for_roundtrip"
    cipher = encrypt_github_token(plaintext)
    assert cipher != plaintext
    assert decrypt_github_token(cipher) == plaintext


def test_roundtrip_derived_key() -> None:
    """SHA-256 derived key path: non-Fernet input is hashed into a valid Fernet key."""
    os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = "test-fernet-key-32-bytes-ok!!!"
    plaintext = "ghp_another_token"
    cipher = encrypt_github_token(plaintext)
    assert decrypt_github_token(cipher) == plaintext


def test_missing_key_raises() -> None:
    os.environ["GITHUB_TOKEN_ENCRYPTION_KEY"] = ""
    with pytest.raises(RuntimeError):
        encrypt_github_token("token")
