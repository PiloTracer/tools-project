"""Bootstrap local superuser when the database is empty."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.services.auth_local import hash_password


async def run_bootstrap(session: AsyncSession) -> None:
    settings = get_settings()
    if not settings.auth_local_enabled:
        return
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return
    exists = await session.scalar(select(User).limit(1))
    if exists is not None:
        return
    email = settings.bootstrap_admin_email.strip().lower()
    user = User(
        email=email,
        password_hash=hash_password(settings.bootstrap_admin_password),
        display_name=settings.bootstrap_admin_display_name,
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
