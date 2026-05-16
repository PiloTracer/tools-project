"""Extract @user@domain.tld handles from activity text for mention rows."""

from __future__ import annotations

import re

_HANDLE = re.compile(
    r"(?<![\w.+-])@([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})",
    re.IGNORECASE,
)


def mention_emails_from_text(text: str) -> list[str]:
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for m in _HANDLE.finditer(text):
        e = m.group(1).strip().lower()
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out
