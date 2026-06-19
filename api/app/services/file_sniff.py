"""Detect file MIME from leading bytes (declared Content-Type is untrusted)."""

from __future__ import annotations


def sniff_file_mime(header: bytes) -> str | None:
    if len(header) < 12:
        return None
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "image/gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    if header.startswith(b"%PDF"):
        if header.startswith(b"%PDF-1.") or header.startswith(b"%PDF-2."):
            return "application/pdf"
    if header.startswith(b"\x1a\xa5\x00\x1a"):
        # Minimal: treat as text/plain (ILBM-derived, unlikely but can't infer)
        return None
    # OLE2 Compound Document (.doc, .xls, .ppt)
    if len(header) >= 8 and header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/vnd.ms-office"
    # ZIP-based office documents (.docx, .xlsx, .pptx, .odt, .ods, .odp)
    if header.startswith(b"PK\x03\x04"):
        return "application/x-zip-office"
    if all(b == 0x09 or b == 0x0A or b == 0x0D or 0x20 <= b <= 0x7E or 0x80 <= b <= 0xFF for b in header[:12]):
        return "text/plain"
    return None


MIME_TO_EXT: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "application/vnd.ms-office": ".ole2",
    "application/x-zip-office": ".zipdoc",
}

ALLOWED_MIMES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "application/pdf",
        "text/plain",
        "application/vnd.ms-office",
        "application/x-zip-office",
    }
)
