"""Bootstrap local superuser when the database is empty."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.services.auth_local import hash_password

logger = logging.getLogger(__name__)


async def run_bootstrap(session: AsyncSession) -> None:
    settings = get_settings()
    if not settings.auth_local_enabled:
        return
    exists = await session.scalar(select(User).limit(1))
    if exists is not None:
        return
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        logger.warning(
            "Database has no users but BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD "
            "are unset — local login and demo SQL seeds that require a superuser will not "
            "be created until you add credentials or create a user manually."
        )
        return
    email = settings.bootstrap_admin_email.strip().lower()
    user = User(
        email=email,
        password_hash=hash_password(settings.bootstrap_admin_password),
        display_name=settings.bootstrap_admin_display_name,
        auth_source="local",
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    logger.info("Bootstrap created local superuser (email=%s)", email)
