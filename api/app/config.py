"""Runtime configuration (env-driven)."""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)

_WEAK_JWT_SECRETS = frozenset({
    "change_me_generate_a_long_random_secret",
    "change_me",
    "",
})
_WEAK_DB_PASSWORDS = frozenset({
    "prj_dev_change_me",
    "change_me",
    "",
})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Auth modes: standalone deploy uses local only; integrated uses OAuth (or both).
    auth_local_enabled: bool = True
    auth_oauth_enabled: bool = True

    database_url: str = (
        "postgresql+asyncpg://prj:prj_dev_change_me@postgresql:5432/tools_project"
    )

    #: Empty string → repo `sql/` (host dev) else `/sql` if mounted in Docker via compose.
    sql_schema_dir: str = ""
    #: When False, skips `sql/*.sql` on startup (e.g. tests); tables must exist.
    sql_schema_apply: bool = True

    jwt_secret: str = "change_me_generate_a_long_random_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h — adjust per policy

    # OAuth: userinfo URL used by the API to resolve SSO access tokens (same as web IdP).
    oauth_user_info_endpoint: str | None = None

    # First superuser when DB is empty (standalone bootstrap). Omit to skip auto-create.
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_display_name: str = "Administrator"

    # Attachments: per-project quota (MVP). Set to 0 for unlimited.
    attachment_max_per_project: int = 500
    # Byte quota: total bytes stored per project (0 = unlimited).
    attachment_max_bytes_per_project: int = 0
    # Retention: number of days after which attachments may be cleaned up by
    # a scheduled job (0 = never delete). The hook point lives in
    # `app/services/attachment_storage.py:retention_cutoff()`.
    attachment_retention_days: int = 0
    # How often the retention purge background loop runs (seconds, default 1h).
    attachment_retention_purge_interval_seconds: int = 3600

    # GitHub (Batch I): background poll + REST page size for commit sync.
    github_sync_enabled: bool = True
    github_poll_interval_seconds: int = 300
    github_poll_initial_delay_seconds: int = 8
    github_commits_per_sync: int = 100


    @classmethod
    def _check_defaults(cls, values: dict) -> dict:
        """Warn (dev) or refuse (production) when secrets match known weak defaults."""
        jwt = values.get("jwt_secret", "")
        if jwt in _WEAK_JWT_SECRETS:
            log.warning(
                "JWT_SECRET matches a known weak default — "
                "anyone can forge tokens. Set a strong random secret in .env."
            )
        db_url = values.get("database_url", "")
        for weak in _WEAK_DB_PASSWORDS:
            if weak and f":{weak}@" in db_url:
                log.warning(
                    "DATABASE_URL password matches a known weak default — "
                    "set a strong password in .env."
                )
                break
        return values


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings._check_defaults(settings.model_dump())
    return settings
