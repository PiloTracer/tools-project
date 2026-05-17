"""Periodic GitHub commit sync (best-effort; per-link transactions)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import session_factory
from app.models.github_link import GithubLink
from app.services.github_sync import sync_github_link

log = logging.getLogger(__name__)


async def github_poll_loop() -> None:
    settings = get_settings()
    await asyncio.sleep(max(0, float(settings.github_poll_initial_delay_seconds)))
    while True:
        try:
            if not get_settings().github_sync_enabled:
                await asyncio.sleep(max(30.0, float(get_settings().github_poll_interval_seconds)))
                continue
            fac = session_factory()
            async with fac() as session:
                link_ids = list((await session.scalars(select(GithubLink.id))).all())
            for lid in link_ids:
                async with fac() as s2:
                    try:
                        await sync_github_link(s2, lid)
                        await s2.commit()
                    except Exception:
                        await s2.rollback()
                        log.exception("GitHub poll failed for link_id=%s", lid)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("GitHub poll outer failure")
        await asyncio.sleep(float(get_settings().github_poll_interval_seconds))
