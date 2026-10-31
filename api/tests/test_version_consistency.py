"""The API version is declared in three places — keep them in lockstep."""

from __future__ import annotations

import tomllib
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_and_main_version_match() -> None:
    with (API_ROOT / "pyproject.toml").open("rb") as handle:
        package_version = tomllib.load(handle)["project"]["version"]

    main_source = (API_ROOT / "app" / "main.py").read_text()

    # FastAPI(version="…") and the /healthz payload ({"version": "…"})
    assert f'version="{package_version}"' in main_source
    assert f'"version": "{package_version}"' in main_source
