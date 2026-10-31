"""Unit tests for the MCP client server — stdlib only, no network.

The canonical module lives at `app/client/mcp_server.py`; consuming repositories
run a byte-identical copy. These tests cover the P0 behaviours of SPEC
amendment 01 (R9/R10.6): the Cloudflare-safe User-Agent, the version handshake,
the self-check, and the no-secret-in-errors rule.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import urllib.error
from pathlib import Path

import pytest

from app.client import mcp_server

UNIT_TEST_KEY = "tools_project_unit_test"


@pytest.fixture(autouse=True)
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_server, "API_KEY", UNIT_TEST_KEY)


@pytest.fixture(autouse=True)
def _reset_capability_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the lazy capability probe isolated per test (it is process-global)."""
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_CHECKED", False)
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_CACHE", None)
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_ERROR", None)


def test_request_headers_send_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_USER_AGENT", raising=False)

    headers = mcp_server._request_headers()

    assert headers["User-Agent"] == f"tools-project-mcp/{mcp_server.SERVER_VERSION}"
    assert headers["X-Api-Key"] == UNIT_TEST_KEY


def test_user_agent_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_USER_AGENT", "custom-agent/9")

    assert mcp_server._request_headers()["User-Agent"] == "custom-agent/9"


def test_no_api_key_header_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_server, "API_KEY", "")

    assert "X-Api-Key" not in mcp_server._request_headers()


def test_initialize_reports_server_version() -> None:
    response = mcp_server._handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})

    assert response is not None
    assert response["result"]["serverInfo"]["version"] == mcp_server.SERVER_VERSION


def test_api_get_error_does_not_leak_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(mcp_server.urllib.request, "urlopen", _boom)

    result = mcp_server._api_get("/v1/agent/projects")

    assert result["ok"] is False
    assert UNIT_TEST_KEY not in str(result)


def test_tool_error_text_does_not_leak_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise urllib.error.URLError("down")

    monkeypatch.setattr(mcp_server.urllib.request, "urlopen", _boom)

    result = mcp_server._handle_tool_call("list_projects", {})

    assert UNIT_TEST_KEY not in result["content"][0]["text"]


def test_self_check_tolerates_old_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server, "_api_get", lambda _path: {"ok": False, "error": "HTTP 404: Not Found"}
    )

    lines, ok = mcp_server.self_check()

    assert ok is True
    assert any("unavailable" in line for line in lines)
    assert any(line.startswith("tools:") for line in lines)


def test_self_check_fails_on_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server, "_api_get", lambda _path: {"ok": False, "error": "HTTP 401: Not authenticated"}
    )

    _lines, ok = mcp_server.self_check()

    assert ok is False


def test_self_check_reports_api_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "_api_get",
        lambda _path: {
            "ok": True,
            "data": {"agent_api_version": "1.1.0", "capabilities": ["ticket_detail"]},
        },
    )

    lines, ok = mcp_server.self_check()

    assert ok is True
    assert any("agent_api_version: 1.1.0" in line for line in lines)
    assert any("ticket_detail" in line for line in lines)


def test_self_check_reports_base_url_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_server, "API_BASE_URL", "https://example.test")
    monkeypatch.setattr(mcp_server, "BASE_URL_SOURCE", "env API_BASE_URL")
    monkeypatch.setattr(mcp_server, "_api_get", lambda _path: {"ok": False, "error": "HTTP 404: x"})

    lines, _ok = mcp_server.self_check()

    assert any("base_url: https://example.test (from env API_BASE_URL)" in line for line in lines)


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp_server.main(["--version"]) == 0

    assert mcp_server.SERVER_VERSION in capsys.readouterr().out


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def test_tools_list_includes_ticket_and_attachment() -> None:
    names = {tool["name"] for tool in mcp_server.TOOLS}

    assert {"get_ticket_detail", "get_attachment", "list_ticket_activities"} <= names


def test_get_ticket_detail_builds_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def _fake(path: str) -> dict[str, object]:
        captured["path"] = path
        return {"ok": True, "data": {"ticket": {}}}

    monkeypatch.setattr(mcp_server, "_api_get", _fake)

    result = mcp_server._handle_tool_call(
        "get_ticket_detail",
        {"ticket": "PZT-T-2", "include_activities": False, "activity_limit": 10},
    )

    assert captured["path"].startswith("/v1/agent/tickets/PZT-T-2?")
    assert "include_activities=False" in captured["path"]
    assert "activity_limit=10" in captured["path"]
    assert json.loads(result["content"][0]["text"])["ok"] is True


def test_get_ticket_detail_accepts_a_web_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def _fake(path: str) -> dict[str, object]:
        captured["path"] = path
        return {"ok": True, "data": {}}

    monkeypatch.setattr(mcp_server, "_api_get", _fake)

    result = mcp_server._handle_tool_call(
        "get_ticket_detail",
        {
            "url": "https://project.cloudsys.win/projects/p/tickets/8fb47f08-8daf-457f-b798-149e8e4eaf60",
            "activity_limit": 10,
        },
    )

    assert captured["path"].startswith("/v1/agent/tickets/resolve?url=")
    assert "https%3A%2F%2Fproject.cloudsys.win" in captured["path"]
    assert "activity_limit=10" in captured["path"]
    assert json.loads(result["content"][0]["text"])["ok"] is True


def test_list_ticket_activities_builds_path(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def _fake(path: str) -> dict[str, object]:
        captured["path"] = path
        return {"ok": True, "data": {"items": []}}

    monkeypatch.setattr(mcp_server, "_api_get", _fake)

    result = mcp_server._handle_tool_call(
        "list_ticket_activities",
        {"ticket": "PZT-T-2", "limit": 5, "offset": 10, "order": "asc"},
    )

    assert captured["path"].startswith("/v1/agent/tickets/PZT-T-2/activities?")
    assert "limit=5" in captured["path"]
    assert "offset=10" in captured["path"]
    assert "order=asc" in captured["path"]
    assert json.loads(result["content"][0]["text"])["ok"] is True


def test_list_ticket_activities_requires_ticket() -> None:
    result = mcp_server._handle_tool_call("list_ticket_activities", {})

    assert json.loads(result["content"][0]["text"])["ok"] is False


def test_get_ticket_detail_requires_ticket() -> None:
    result = mcp_server._handle_tool_call("get_ticket_detail", {})

    payload = json.loads(result["content"][0]["text"])
    assert payload["ok"] is False
    assert "ticket" in payload["error"]


def test_get_attachment_returns_image_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "_api_get_binary",
        lambda _path: (PNG_BYTES, {"content-type": "image/png"}, None),
    )

    result = mcp_server._handle_tool_call("get_attachment", {"attachment_id": "abc"})

    blocks = result["content"]
    assert blocks[0]["type"] == "text"
    meta = json.loads(blocks[0]["text"])
    assert meta["ok"] is True
    assert meta["delivery"] == "inline_image"
    assert meta["mime"] == "image/png"
    assert meta["sha256"] == hashlib.sha256(PNG_BYTES).hexdigest()
    assert blocks[1] == {
        "type": "image",
        "data": base64.b64encode(PNG_BYTES).decode("ascii"),
        "mimeType": "image/png",
    }


def test_get_attachment_returns_text_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "_api_get_binary",
        lambda _path: (b"hello evidence", {"content-type": "text/plain"}, None),
    )

    result = mcp_server._handle_tool_call("get_attachment", {"attachment_id": "abc"})

    blocks = result["content"]
    assert json.loads(blocks[0]["text"])["delivery"] == "inline_text"
    assert blocks[1] == {"type": "text", "text": "hello evidence"}


def test_get_attachment_oversize_saves_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES", "8")
    monkeypatch.setattr(
        mcp_server,
        "_api_get_binary",
        lambda _path: (
            PNG_BYTES,
            {"content-type": "image/png", "content-disposition": 'inline; filename="shot.png"'},
            None,
        ),
    )

    result = mcp_server._handle_tool_call(
        "get_attachment", {"attachment_id": "abc", "save_dir": str(tmp_path)}
    )

    assert len(result["content"]) == 1
    meta = json.loads(result["content"][0]["text"])
    assert meta["delivery"] == "saved_file"
    saved = Path(meta["path"])
    assert saved.exists() and saved.read_bytes() == PNG_BYTES
    assert saved.name == "shot.png"
    assert saved.parent == tmp_path.resolve()


def test_get_attachment_sanitizes_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES", "8")
    monkeypatch.setattr(
        mcp_server,
        "_api_get_binary",
        lambda _path: (
            PNG_BYTES,
            {"content-type": "image/png", "content-disposition": 'attachment; filename="../../evil.png"'},
            None,
        ),
    )

    result = mcp_server._handle_tool_call(
        "get_attachment", {"attachment_id": "abc", "save_dir": str(tmp_path)}
    )

    saved = Path(json.loads(result["content"][0]["text"])["path"])
    assert saved.parent == tmp_path.resolve()
    assert ".." not in saved.name


def test_get_attachment_error_includes_status_and_request_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mcp_server,
        "_api_get_binary",
        lambda _path: (
            None,
            {"x-request-id": "req-123"},
            {
                "ok": False,
                "status": 404,
                "error": "HTTP 404: attachment_not_found",
                "request_id": "req-123",
                "hint": mcp_server._STATUS_HINTS[404],
            },
        ),
    )

    result = mcp_server._handle_tool_call("get_attachment", {"attachment_id": "abc"})

    payload = json.loads(result["content"][0]["text"])
    assert payload["ok"] is False
    assert payload["status"] == 404
    assert payload["request_id"] == "req-123"
    assert "attachment_not_found" in payload["error"]
    assert payload["hint"]


def _http_error(
    code: int, body: bytes = b"", headers: dict[str, str] | None = None
) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "http://test/v1/agent/tickets/x",
        code,
        "error",
        headers or {},
        io.BytesIO(body),
    )


def test_api_get_http_error_includes_status_request_id_and_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise _http_error(
            404,
            b'{"detail": "ticket_not_found"}',
            {"x-request-id": "req-abc"},
        )

    monkeypatch.setattr(mcp_server.urllib.request, "urlopen", _boom)

    result = mcp_server._api_get("/v1/agent/tickets/x")

    assert result["ok"] is False
    assert result["status"] == 404
    assert result["request_id"] == "req-abc"
    assert result["error"] == "HTTP 404: ticket_not_found"
    assert "superuser" not in result["error"]


def test_api_get_cloudflare_html_403_is_explained(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise _http_error(403, b"<html><title>Error 1010: Access denied</title></html>")

    monkeypatch.setattr(mcp_server.urllib.request, "urlopen", _boom)

    result = mcp_server._api_get("/v1/agent/projects")

    assert result["ok"] is False
    assert result["status"] == 403
    assert "edge/CDN" in result["error"]
    assert "MCP_USER_AGENT" in result["hint"]


# ── P2: lazy capability probe / graceful degradation ──────────────────


def _reset_capabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_CHECKED", False)
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_CACHE", None)
    monkeypatch.setattr(mcp_server, "_CAPABILITIES_ERROR", None)


def test_tools_are_hidden_on_an_older_api(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_capabilities(monkeypatch)
    monkeypatch.setattr(
        mcp_server,
        "_api_get",
        lambda _path: {"ok": True, "data": {"agent_api_version": "1.0.0"}},
    )

    enabled = {tool["name"] for tool in mcp_server._enabled_tools()}
    response = mcp_server._handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )

    assert enabled == mcp_server._BASE_TOOL_NAMES
    assert response is not None
    assert {tool["name"] for tool in response["result"]["tools"]} == (
        mcp_server._BASE_TOOL_NAMES
    )


def test_tools_are_fully_enabled_on_1_1(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_capabilities(monkeypatch)
    monkeypatch.setattr(
        mcp_server,
        "_api_get",
        lambda _path: {"ok": True, "data": {"agent_api_version": "1.1.0"}},
    )

    assert mcp_server._enabled_tools() == mcp_server.TOOLS


def test_tools_stay_enabled_when_capabilities_endpoint_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_capabilities(monkeypatch)
    monkeypatch.setattr(
        mcp_server,
        "_api_get",
        lambda _path: {"ok": False, "error": "HTTP 404: Not Found"},
    )

    assert mcp_server._enabled_tools() == mcp_server.TOOLS

    lines, ok = mcp_server.self_check()
    assert ok is True
    assert any("unavailable" in line for line in lines)
    assert any("get_ticket_detail" in line for line in lines)


def test_capability_probe_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_capabilities(monkeypatch)
    calls: list[str] = []

    def _fake(path: str) -> dict[str, object]:
        calls.append(path)
        return {"ok": True, "data": {"agent_api_version": "1.1.0"}}

    monkeypatch.setattr(mcp_server, "_api_get", _fake)

    mcp_server._enabled_tools()
    mcp_server._enabled_tools()
    mcp_server.self_check()

    assert calls == ["/v1/agent/capabilities"]
