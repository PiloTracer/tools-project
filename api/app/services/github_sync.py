"""Fetch commits from GitHub REST API and upsert into github_commits (html_url always set)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.github_commit import GithubCommit
from app.models.github_link import GithubLink
from app.services.github_token_crypto import decrypt_github_token

log = logging.getLogger(__name__)


def _derive_commit_html_url(owner: str, repo: str, sha: str, api_html_url: str | None) -> str:
    """Prefer GitHub API html_url; otherwise canonical github.com commit URL."""
    u = (api_html_url or "").strip()
    if u.startswith("http://") or u.startswith("https://"):
        return u
    o = owner.strip()
    r = repo.strip()
    s = sha.strip()
    return f"https://github.com/{o}/{r}/commit/{s}"


def _parse_committed_at(commit_blob: dict[str, Any]) -> datetime:
    author = (commit_blob.get("author") or {}) if isinstance(commit_blob.get("author"), dict) else {}
    date_s = author.get("date")
    if isinstance(date_s, str):
        try:
            if date_s.endswith("Z"):
                date_s = date_s[:-1] + "+00:00"
            return datetime.fromisoformat(date_s)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


async def sync_github_link(db: AsyncSession, link_id: uuid.UUID) -> dict[str, int | str | None]:
    """Pull latest commits for one link; upsert rows with required html_url."""
    link = await db.get(GithubLink, link_id)
    if link is None:
        raise ValueError("github link not found")

    token = decrypt_github_token(link.token_cipher)
    owner = link.owner.strip()
    repo = link.repo.strip()
    settings = get_settings()
    per_page = min(100, max(1, settings.github_commits_per_sync))

    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.get(url, headers=headers, params={"per_page": per_page})
        if resp.status_code == 401:
            raise PermissionError("GitHub rejected the token (401)")
        if resp.status_code == 404:
            raise FileNotFoundError(f"GitHub repo not found: {owner}/{repo}")
        resp.raise_for_status()
        items = resp.json()

    if not isinstance(items, list):
        raise ValueError("Unexpected GitHub API response")

    upserted = 0
    commits_info: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sha = item.get("sha")
        if not isinstance(sha, str) or len(sha) < 7:
            continue
        # API returns full SHA on first line sometimes "sha\ntree ..."
        sha_full = sha.split()[0][:40]
        commit_obj = item.get("commit")
        if not isinstance(commit_obj, dict):
            commit_obj = {}
        message = commit_obj.get("message") or ""
        if not isinstance(message, str):
            message = str(message)
        author_block = commit_obj.get("author")
        author_name = author_block.get("name") if isinstance(author_block, dict) else None
        author_email = author_block.get("email") if isinstance(author_block, dict) else None
        if author_name is not None and not isinstance(author_name, str):
            author_name = str(author_name)
        if author_email is not None and not isinstance(author_email, str):
            author_email = str(author_email)

        committed_at = _parse_committed_at(commit_obj)
        api_html = item.get("html_url")
        html_url = _derive_commit_html_url(owner, repo, sha_full, api_html if isinstance(api_html, str) else None)

        stmt = (
            pg_insert(GithubCommit)
            .values(
                id=uuid.uuid4(),
                github_link_id=link.id,
                sha=sha_full,
                message=message,
                author_name=author_name,
                author_email=author_email,
                committed_at=committed_at,
                html_url=html_url,
                raw_json=item,
            )
            .on_conflict_do_update(
                index_elements=[GithubCommit.github_link_id, GithubCommit.sha],
                set_={
                    "message": message,
                    "author_name": author_name,
                    "author_email": author_email,
                    "committed_at": committed_at,
                    "html_url": html_url,
                    "raw_json": item,
                },
            )
        )
        await db.execute(stmt)
        upserted += 1
        commits_info.append({
            "sha": sha_full,
            "html_url": html_url,
            "message": message,
        })

    link.last_synced_at = datetime.now(timezone.utc)
    if items and isinstance(items[0], dict):
        s0 = items[0].get("sha")
        if isinstance(s0, str) and s0:
            link.last_seen_sha = s0.split()[0][:40]
    await db.flush()

    return {"upserted": upserted, "owner": owner, "repo": repo, "commits": commits_info}
