#!/usr/bin/env python3
"""MCP server for tools-project read-only agent queries.

Protocol: Model Context Protocol (JSON-RPC 2.0) over stdio.

Usage:
  python3 mcp_server.py                 # serve over stdio
  python3 mcp_server.py --version       # print the server version
  python3 mcp_server.py --self-check    # print config + API capabilities, exit non-zero on failure

Auth (resolved in order):
  1. Env var TOOLS_PROJECT_API_KEY   — personal key, remote-ready
  2. File ~/.tools-project-key       — optional `BASE_URL=<url>` line plus one key line
  3. Env var AGENT_API_KEY           — legacy shared secret (deprecated)

Base URL (resolved in order):
  1. Env var API_BASE_URL
  2. `BASE_URL=<url>` line in ~/.tools-project-key
  3. http://localhost:8300

The canonical copy lives at `api/app/client/mcp_server.py` in the tools-project
repository and is served by the deployed API (agent API 1.1.0+); each consuming
repository runs its own copy at `.opencode/mcp/project-mcp/mcp_server.py`.

The hosted deployment sits behind Cloudflare, which answers urllib's default
User-Agent with HTTP 403 (Error 1010), so every request identifies itself as
`tools-project-mcp/<SERVER_VERSION>` (override: MCP_USER_AGENT). Keep this
header when copying the file into a consuming repository.
"""

import base64
import contextlib
import hashlib
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "tools-project-agent") or "tools-project-agent"
SERVER_VERSION = "1.1.0"


def _read_key_file() -> list[str]:
    """Return the non-empty lines of ~/.tools-project-key (empty when absent)."""
    key_file = Path.home() / ".tools-project-key"
    if not key_file.is_file():
        return []
    try:
        return [line.strip() for line in key_file.read_text().splitlines() if line.strip()]
    except OSError:
        return []


def _resolve_api_key() -> str:
    key = os.environ.get("TOOLS_PROJECT_API_KEY", "").strip()
    if key:
        return key

    for line in _read_key_file():
        if not line.startswith("BASE_URL="):
            return line

    return os.environ.get("AGENT_API_KEY", "").strip()


def _resolve_base_url() -> tuple[str, str]:
    """Return (url, human-readable source) for the API base URL."""
    url = os.environ.get("API_BASE_URL", "").strip()
    if url:
        return url.rstrip("/"), "env API_BASE_URL"

    for line in _read_key_file():
        if line.startswith("BASE_URL="):
            value = line.removeprefix("BASE_URL=").strip().rstrip("/")
            if value:
                return value, "key file BASE_URL"

    return "http://localhost:8300", "default (no API_BASE_URL / key-file BASE_URL)"


BASE_URL_VALUE, BASE_URL_SOURCE = _resolve_base_url()
API_BASE_URL = BASE_URL_VALUE
API_KEY = _resolve_api_key()

TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_projects",
        "description": "List all projects with summary stats (open tasks, open tickets, member count). Returns JSON array.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_project_context",
        "description": "Full project context: details, tasks, tickets, members, linked clients, GitHub refs. Returns JSON object.",
        "inputSchema": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "description": "UUID of the project"}},
            "required": ["project_id"],
        },
    },
    {
        "name": "get_task_info",
        "description": "List tasks, optionally filtered by ref (e.g. TPR-3) or status. Returns JSON array.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Task ref to filter by (e.g. TPR-3)"},
                "status": {"type": "string", "description": "Task status filter"},
                "limit": {"type": "integer", "description": "Max results (default 50, max 200)"},
            },
        },
    },
    {
        "name": "get_ticket_info",
        "description": "List tickets, optionally filtered by ref (e.g. TPR-T-12) or status. Returns JSON array.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Ticket ref to filter by (e.g. TPR-T-12)"},
                "status": {"type": "string", "description": "Ticket status filter"},
                "limit": {"type": "integer", "description": "Max results (default 50, max 200)"},
            },
        },
    },
    {
        "name": "search_entities",
        "description": "Unified search across projects, tasks, tickets, clients, and prospects. Returns JSON array of hits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Search term"},
                "limit": {"type": "integer", "description": "Max results (default 20, max 50)"},
            },
            "required": ["q"],
        },
    },
    {
        "name": "get_ticket_detail",
        "description": "Full ticket detail: people, counts, attachments with download URLs, resolved description, the most recent activity/comment page, linked commits. Pass a ticket UUID/ref or a copied web ticket URL (agent API 1.1.0+).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket": {"type": "string", "description": "Ticket UUID or ref (e.g. PZT-T-2)"},
                "url": {"type": "string", "description": "Web ticket URL instead of ticket, e.g. https://host/projects/<p>/tickets/<uuid>"},
                "include_activities": {"type": "boolean", "description": "Include the first activity page (default true)"},
                "include_internal": {"type": "boolean", "description": "Include staff-only internal notes (default true)"},
                "activity_limit": {"type": "integer", "description": "Activities in the first page (default 50, max 200, newest first)"},
            },
        },
    },
    {
        "name": "list_ticket_activities",
        "description": "Paginated ticket activity/comment feed (newest first by default), including per-comment attachments and meta_json. Use the ticket UUID/ref and offset/next_offset for older pages (agent API 1.1.0+).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket": {"type": "string", "description": "Ticket UUID or ref (e.g. PZT-T-2)"},
                "limit": {"type": "integer", "description": "Page size (default 50, max 200)"},
                "offset": {"type": "integer", "description": "Number of newest activities to skip (default 0)"},
                "order": {"type": "string", "enum": ["asc", "desc"], "description": "desc = newest first (default)"},
                "kind": {"type": "string", "description": "Filter by activity kind (comment, status_change, …)"},
                "include_internal": {"type": "boolean", "description": "Include staff-only internal notes (default true)"},
            },
            "required": ["ticket"],
        },
    },
    {
        "name": "get_attachment",
        "description": "Fetch one attachment (screenshot/PDF/text) by id. Returns an image block for images, text for small text files, otherwise saves the file and returns its path + sha256 (agent API 1.1.0+).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "attachment_id": {"type": "string", "description": "Attachment UUID"},
                "save_dir": {"type": "string", "description": "Directory for files too large to inline (default ~/.cache/tools-project/attachments)"},
            },
            "required": ["attachment_id"],
        },
    },
]


def _user_agent() -> str:
    """Cloudflare-safe User-Agent (urllib's default is rejected with 403 on the hosted API)."""
    override = os.environ.get("MCP_USER_AGENT", "").strip()
    return override or f"tools-project-mcp/{SERVER_VERSION}"


def _request_headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": _user_agent()}
    if API_KEY:
        headers["X-Api-Key"] = API_KEY
    return headers


_STATUS_HINTS = {
    401: "check TOOLS_PROJECT_API_KEY or ~/.tools-project-key (the key may be revoked)",
    403: "the key owner must be a superuser; an HTML body means the edge blocked the request — set a non-default User-Agent",
    404: "not found: the ticket/attachment does not exist, or the deployment predates agent API 1.1.0",
    409: "conflict: retrying with the same idempotency key and a different payload",
    429: "rate limited: retry later",
    500: "server error: retry later and quote the request id",
}


def _error_payload(code: int, body: str, headers: dict[str, str]) -> dict[str, Any]:
    """Turn an HTTP error into a consumer-friendly payload (status, request id, hint)."""
    text = (body or "").strip()
    hint = _STATUS_HINTS.get(code, "")

    if text.startswith("<") or "cloudflare" in text.lower():
        text = "edge/CDN blocked the request (HTML response)"
        hint = "set MCP_USER_AGENT to a non-default value; urllib's default is rejected with 403"
    else:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            text = text[:300]
        else:
            detail = parsed.get("detail") if isinstance(parsed, dict) else None
            if isinstance(detail, str):
                text = detail
            elif detail is not None:
                text = json.dumps(detail)

    payload: dict[str, Any] = {
        "ok": False,
        "status": code,
        "error": f"HTTP {code}: {text}"[:500],
    }
    request_id = headers.get("x-request-id")
    if request_id:
        payload["request_id"] = request_id
    if hint:
        payload["hint"] = hint
    return payload


def _api_get(path: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"

    req = urllib.request.Request(url, headers=_request_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if e.fp else ""
        headers = {k.lower(): v for k, v in (getattr(e, "headers", None) or {}).items()}
        return _error_payload(e.code, body, headers)
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": f"Connection failed: {e.reason}",
            "hint": "check API_BASE_URL and network access to the deployment",
        }
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid JSON response: {e}", "hint": "the endpoint may be behind a proxy"}




def _build_query(params: dict[str, Any], allowed: set[str]) -> str:
    parts: list[str] = []
    for k, v in params.items():
        if k in allowed and v is not None:
            parts.append(f"{k}={quote(str(v))}")
    return ("?" + "&".join(parts)) if parts else ""



def _inline_image_max_bytes() -> int:
    try:
        return int(os.environ.get("TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES", str(5 * 1024 * 1024)))
    except ValueError:
        return 5 * 1024 * 1024


def _inline_text_max_bytes() -> int:
    try:
        return int(os.environ.get("TOOLS_PROJECT_INLINE_TEXT_MAX_BYTES", str(1024 * 1024)))
    except ValueError:
        return 1024 * 1024


def _default_save_dir() -> Path:
    cache = Path.home() / ".cache" / "tools-project" / "attachments"
    try:
        cache.mkdir(parents=True, exist_ok=True)
        os.chmod(cache, 0o700)
        return cache
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "tools-project" / "attachments"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _safe_name(name: str, fallback: str) -> str:
    candidate = Path(name.strip()).name.replace("..", "").strip()
    return candidate[:200] if candidate else fallback


def _filename_from_headers(headers: dict[str, str], fallback: str) -> str:
    disposition = headers.get("content-disposition", "")
    if "filename*=utf-8''" in disposition:
        raw = disposition.split("filename*=utf-8''", 1)[1].split(";")[0].strip().strip('"')
        return _safe_name(unquote(raw), fallback)
    if 'filename="' in disposition:
        raw = disposition.split('filename="', 1)[1].split('"', 1)[0]
        return _safe_name(raw, fallback)
    return fallback


def _api_get_binary(path: str) -> tuple[bytes | None, dict[str, str], dict[str, Any] | None]:
    """Return (body, response headers, error payload)."""
    url = f"{API_BASE_URL}{path}"
    headers = _request_headers()
    headers["Accept"] = "*/*"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return body, resp_headers, None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if e.fp else ""
        resp_headers = {k.lower(): v for k, v in (getattr(e, "headers", None) or {}).items()}
        return None, resp_headers, _error_payload(e.code, body, resp_headers)
    except urllib.error.URLError as e:
        return None, {}, {
            "ok": False,
            "error": f"Connection failed: {e.reason}",
            "hint": "check API_BASE_URL and network access to the deployment",
        }


def _save_attachment(data: bytes, filename: str, save_dir: str | None) -> Path:
    directory = Path(save_dir).expanduser().resolve() if save_dir else _default_save_dir()
    directory.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(directory, 0o700)

    target = directory / filename
    suffix = target.suffix
    stem = target.stem
    counter = 1
    while target.exists():
        target = directory / f"{stem}-{counter}{suffix}"
        counter += 1

    resolved = target.resolve()
    if not str(resolved).startswith(str(directory.resolve()) + os.sep) and resolved != directory.resolve():
        raise ValueError("refusing to write outside the save directory")

    target.write_bytes(data)
    return target


def _attachment_result(
    attachment_id: str,
    *,
    save_dir: str | None = None,
) -> dict[str, Any]:
    data, headers, error = _api_get_binary(f"/v1/agent/attachments/{quote(attachment_id)}")
    if error is not None or data is None:
        payload = error or {"ok": False, "error": "attachment unavailable"}
        return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}

    mime = headers.get("content-type", "application/octet-stream").split(";")[0].strip()
    filename = _filename_from_headers(headers, f"attachment-{attachment_id}")
    digest = hashlib.sha256(data).hexdigest()

    metadata: dict[str, Any] = {
        "ok": True,
        "attachment_id": attachment_id,
        "filename": filename,
        "mime": mime,
        "size_bytes": len(data),
        "sha256": digest,
    }
    content: list[dict[str, Any]] = []

    if mime.startswith("image/") and len(data) <= _inline_image_max_bytes():
        metadata["delivery"] = "inline_image"
        content.append({"type": "text", "text": json.dumps(metadata, indent=2)})
        content.append({"type": "image", "data": base64.b64encode(data).decode("ascii"), "mimeType": mime})
        return {"content": content}

    if mime == "text/plain" and len(data) <= _inline_text_max_bytes():
        metadata["delivery"] = "inline_text"
        content.append({"type": "text", "text": json.dumps(metadata, indent=2)})
        content.append({"type": "text", "text": data.decode("utf-8", errors="replace")})
        return {"content": content}

    try:
        path = _save_attachment(data, _safe_name(filename, f"attachment-{attachment_id}"), save_dir)
    except (OSError, ValueError) as exc:
        return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": f"Save failed: {exc}"}, indent=2)}]}

    metadata["delivery"] = "saved_file"
    metadata["path"] = str(path)
    content.append({"type": "text", "text": json.dumps(metadata, indent=2)})
    return {"content": content}


def _handle_tool_call(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}

    if name == "list_projects":
        result = _api_get("/v1/agent/projects")

    elif name == "get_project_context":
        pid = args.get("project_id", "")
        if not pid:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "project_id is required"}, indent=2)}]}
        result = _api_get(f"/v1/agent/projects/{quote(str(pid))}/context")

    elif name == "get_task_info":
        qs = _build_query(args, {"ref", "status", "limit"})
        result = _api_get(f"/v1/agent/tasks{qs}")

    elif name == "get_ticket_info":
        qs = _build_query(args, {"ref", "status", "limit"})
        result = _api_get(f"/v1/agent/tickets{qs}")

    elif name == "search_entities":
        q = args.get("q", "")
        if not q:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "search term 'q' is required"}, indent=2)}]}
        limit = args.get("limit", 20)
        result = _api_get(f"/v1/agent/search?q={quote(str(q))}&limit={limit}")

    elif name == "get_ticket_detail":
        ticket_ref = args.get("ticket", "")
        ticket_url = args.get("url", "")
        if not ticket_ref and not ticket_url:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "ticket or url is required"}, indent=2)}]}
        qs = _build_query(
            args,
            {"include_activities", "include_internal", "activity_limit"},
        )
        if ticket_url:
            result = _api_get(f"/v1/agent/tickets/resolve?url={quote(str(ticket_url), safe='')}{qs.replace('?', '&', 1)}")
        else:
            result = _api_get(f"/v1/agent/tickets/{quote(str(ticket_ref))}{qs}")

    elif name == "list_ticket_activities":
        ticket_ref = args.get("ticket", "")
        if not ticket_ref:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "ticket is required"}, indent=2)}]}
        qs = _build_query(args, {"limit", "offset", "order", "kind", "include_internal"})
        result = _api_get(f"/v1/agent/tickets/{quote(str(ticket_ref))}/activities{qs}")

    elif name == "get_attachment":
        attachment_id = args.get("attachment_id", "")
        if not attachment_id:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "attachment_id is required"}, indent=2)}]}
        return _attachment_result(str(attachment_id), save_dir=args.get("save_dir"))

    else:
        result = {"ok": False, "error": f"Unknown tool: {name}"}

    return {
        "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
    }


def _handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method", "")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "capabilities": {"tools": {}},
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS},
        }

    if method == "tools/call":
        tool_name = msg.get("params", {}).get("name", "")
        arguments = msg.get("params", {}).get("arguments", {})
        result = _handle_tool_call(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def self_check() -> tuple[list[str], bool]:
    """Return (report lines, ok). ok is False on auth/connection failure.

    A 404 on /v1/agent/capabilities is not a failure: it means the deployed API
    predates agent API 1.1.0, and the older tools still work.
    """
    lines = [
        f"server: {SERVER_NAME} {SERVER_VERSION}",
        f"base_url: {API_BASE_URL} (from {BASE_URL_SOURCE})",
        f"api_key: {'set' if API_KEY else 'missing'}",
    ]
    ok = True

    result = _api_get("/v1/agent/capabilities")
    if result.get("ok"):
        data = result.get("data") or {}
        lines.append(f"agent_api_version: {data.get('agent_api_version', 'unknown')}")
        capabilities = data.get("capabilities") or []
        if capabilities:
            lines.append("capabilities: " + ", ".join(str(item) for item in capabilities))
    else:
        error = str(result.get("error", ""))
        if error.startswith("HTTP 404"):
            lines.append("capabilities: unavailable (deployed API predates agent API 1.1.0)")
        else:
            ok = False
            lines.append(f"capabilities: error - {error[:200]}")

    lines.append("tools: " + ", ".join(str(tool.get("name", "?")) for tool in TOOLS))
    return lines, ok


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--version" in args:
        print(f"{SERVER_NAME} {SERVER_VERSION}")
        return 0

    if "--self-check" in args:
        lines, ok = self_check()
        print("\n".join(lines))
        return 0 if ok else 1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = _handle_request(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
