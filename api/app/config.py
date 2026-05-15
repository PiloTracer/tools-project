"""Runtime configuration (env-driven)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    jwt_secret: str = "change_me_generate_a_long_random_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h — adjust per policy

    # OAuth: userinfo URL used by the API to resolve SSO access tokens (same as web IdP).
    oauth_user_info_endpoint: str | None = None

    # First superuser when DB is empty (standalone bootstrap). Omit to skip auto-create.
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_display_name: str = "Administrator"


@lru_cache
def get_settings() -> Settings:
    return Settings()
