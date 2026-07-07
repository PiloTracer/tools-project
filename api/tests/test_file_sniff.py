"""Tests for file MIME sniffing helper."""

from __future__ import annotations

from app.services.file_sniff import MIME_TO_EXT, sniff_file_mime


def test_sniff_png() -> None:
    assert sniff_file_mime(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4) == "image/png"


def test_sniff_jpeg() -> None:
    assert sniff_file_mime(b"\xff\xd8\xff" + b"\x00" * 9) == "image/jpeg"


def test_sniff_gif() -> None:
    assert sniff_file_mime(b"GIF89a" + b"\x00" * 6) == "image/gif"


def test_sniff_webp() -> None:
    header = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 4
    assert sniff_file_mime(header) == "image/webp"


def test_sniff_pdf() -> None:
    assert sniff_file_mime(b"%PDF-1.4" + b"\x00" * 4) == "application/pdf"


def test_sniff_text() -> None:
    assert sniff_file_mime(b"Hello world!") == "text/plain"


def test_header_too_short() -> None:
    assert sniff_file_mime(b"\x00\x00") is None


def test_mime_to_ext_coverage() -> None:
    for mime in MIME_TO_EXT:
        assert MIME_TO_EXT[mime].startswith(".")
