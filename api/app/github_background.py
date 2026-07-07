"""Periodic GitHub commit sync (best-effort; per-link transactions)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.db import session_factory
from app.models.github_link import GithubLink
from app.services.activity_writer import write_activity
from app.services.attachment_service import run_attachment_retention_purge
from app.services.commit_ref_pending_processor import process_pending_commit_refs
from app.services.github_sync import sync_github_link

log = logging.getLogger(__name__)


async def github_poll_loop() -> None:
    settings = get_settings()
    await asyncio.sleep(max(0, float(settings.github_poll_initial_delay_seconds)))
    while True:
        try:
            # Process pending commit refs (post-commit hook → instant local linking).
            # This runs regardless of github_sync_enabled — it's independent.
            fac = session_factory()
            async with fac() as pending_session:
                await process_pending_commit_refs(pending_session)
                await pending_session.commit()

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
                            body_md = f"{c['sha'][:7]} {result['owner']}/{result['repo']} {preview}"
                            meta: dict[str, object] = {
                                "link_id": str(lid),
                                "sha": c["sha"],
                                "owner": result["owner"],
                                "repo": result["repo"],
                                "html_url": c["html_url"],
                                "message_preview": preview,
                                "full_message": c["message"],
                            }
                            if c.get("id"):
                                meta["commit_id"] = c["id"]
                            if result.get("linked_refs"):
                                meta["linked_refs"] = int(result["linked_refs"])
                            await write_activity(
                                db=s2,
                                project_id=link.project_id,
                                subject_type="project",
                                subject_id=link.project_id,
                                kind="github_commit",
                                actor_id=None,
                                body=body_md,
                                meta_json=meta,
                                is_internal=False,
                            )
                        link.sync_status = "idle"
                        link.last_error = None
                        link.last_error_at = None
                        link.error_count = 0
                        await s2.commit()
                    except PermissionError as exc:
                        await s2.rollback()
                        log.warning("GitHub auth failed for link_id=%s: %s", lid, exc)
                        async with fac() as err_s:
                            err_link = await err_s.get(GithubLink, lid)
                            if err_link is not None:
                                err_link.sync_status = "auth_error"
                                err_link.last_error = str(exc)[:400]
                                err_link.last_error_at = datetime.now(UTC)
                                err_link.error_count = (err_link.error_count or 0) + 1
                                await err_s.commit()
                    except Exception as exc:
                        await s2.rollback()
                        log.exception("GitHub poll failed for link_id=%s", lid)
                        # Persist error state in a fresh transaction
                        async with fac() as err_s:
                            err_link = await err_s.get(GithubLink, lid)
                            if err_link is not None:
                                err_link.sync_status = "error"
                                err_link.last_error = str(exc)[:400]
                                err_link.last_error_at = datetime.now(UTC)
                                err_link.error_count = (err_link.error_count or 0) + 1
                                await err_s.commit()
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


async def attachment_retention_purge_loop() -> None:
    """Background loop that periodically purges expired attachments.

    Runs independently of the GitHub poll loop and ``github_sync_enabled``.
    Sleeps ``attachment_retention_purge_interval_seconds`` between cycles.
    Exits immediately if ``attachment_retention_days`` is 0 or not set.
    """
    settings = get_settings()
    if settings.attachment_retention_days <= 0:
        return

    while True:
        try:
            fac = session_factory()
            async with fac() as session:
                purged = await run_attachment_retention_purge(session)
                if purged:
                    log.info("Purge removed %s expired attachments", purged)
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Attachment retention purge loop error")
        await asyncio.sleep(max(60.0, float(settings.attachment_retention_purge_interval_seconds)))
