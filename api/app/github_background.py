"""Periodic GitHub commit sync (best-effort; per-link transactions)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import session_factory
from app.models.github_link import GithubLink
from app.services.activity_writer import write_activity
from app.services.attachment_service import run_attachment_retention_purge
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
                        link = await s2.get(GithubLink, lid)
                        if link is None:
                            continue
                        result = await sync_github_link(s2, lid)
                        for c in result.get("commits", []):
                            if not c.get("is_new"):
                                continue
                            preview = (c["message"] or "").split("\n")[0][:100]
                            body_md = (
                                f"[`{c['sha'][:7]}`]({c['html_url']}) "
                                f"**{result['owner']}/{result['repo']}** {preview}"
                            )
                            await write_activity(
                                db=s2,
                                project_id=link.project_id,
                                subject_type="project",
                                subject_id=link.project_id,
                                kind="github_commit",
                                actor_id=None,
                                body=body_md,
                                meta_json={
                                    "link_id": str(lid),
                                    "commit_id": c["sha"],
                                    "sha": c["sha"],
                                    "owner": result["owner"],
                                    "repo": result["repo"],
                                    "html_url": c["html_url"],
                                    "message_preview": preview,
                                },
                                is_internal=True,
                            )
                        await s2.commit()
                    except Exception:
                        await s2.rollback()
                        log.exception("GitHub poll failed for link_id=%s", lid)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("GitHub poll outer failure")

        try:
            fac = session_factory()
            async with fac() as purge_session:
                purged = await run_attachment_retention_purge(purge_session)
                if purged:
                    log.info("Attachment retention purge removed %s expired attachments", purged)
                await purge_session.commit()
        except Exception:
            log.exception("Attachment retention purge failed")

        await asyncio.sleep(float(get_settings().github_poll_interval_seconds))
