#!/usr/bin/env python3
"""MCP server for tools-project read-only agent queries.

Protocol: Model Context Protocol (JSON-RPC 2.0) over stdio.

Usage:
  python3 .opencode/mcp/project-mcp/mcp_server.py

Auth (resolved in order):
  1. Env var TOOLS_PROJECT_API_KEY        — personal key, remote-ready
  2. File ~/.tools-project-key             — one-line key, permanent, no exports
  3. Env var AGENT_API_KEY                — legacy shared secret (deprecated)

API_BASE_URL defaults to http://localhost:8300.
Override with the env var or put BASE_URL=<url> as line 1 of the key file.

Setup — pick one:

  # Option A: permanent file (recommended)
  echo "tools_project_<secret>" > ~/.tools-project-key
  chmod 600 ~/.tools-project-key

  # Option B: env var (one-off, good for CI)
  export TOOLS_PROJECT_API_KEY=tools_project_<secret>

  # For remote deployments with Option A, add BASE_URL as first line:
  echo "BASE_URL=https://project.cloudsys.win" > ~/.tools-project-key
  echo "tools_project_<secret>" >> ~/.tools-project-key
  chmod 600 ~/.tools-project-key
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _resolve_api_key() -> str:
    key = os.environ.get("TOOLS_PROJECT_API_KEY", "")
    if key:
        return key

    key_file = Path.home() / ".tools-project-key"
    if key_file.is_file():
        try:
            for line in key_file.read_text().splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("BASE_URL="):
                    return stripped
        except OSError:
            pass

    return os.environ.get("AGENT_API_KEY", "")


def _resolve_base_url() -> str:
    url = os.environ.get("API_BASE_URL", "")
    if url:
        return url

    key_file = Path.home() / ".tools-project-key"
    if key_file.is_file():
        try:
            for line in key_file.read_text().splitlines():
                stripped = line.strip()
                if stripped.startswith("BASE_URL="):
                    return stripped.removeprefix("BASE_URL=").strip()
        except OSError:
            pass

    return "http://localhost:8300"


API_BASE_URL = _resolve_base_url()
API_KEY = _resolve_api_key()
SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "tools-project-agent")

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
]

TOOL_ENDPOINTS: dict[str, str] = {
    "list_projects": "/v1/agent/projects",
    "get_project_context": "/v1/agent/projects/{project_id}/context",
    "get_task_info": "/v1/agent/tasks",
    "get_ticket_info": "/v1/agent/tickets",
    "search_entities": "/v1/agent/search",
}


def _api_get(path: str) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"
    headers = {"Accept": "application/json"}

    if API_KEY:
        headers["X-Api-Key"] = API_KEY

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else "{}"
        detail = body[:500]
        return {"ok": False, "error": f"HTTP {e.code}: {detail}"}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Connection failed: {e.reason}"}
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"Invalid JSON response: {e}"}


def _build_query(params: dict[str, Any], allowed: set[str]) -> str:
    parts: list[str] = []
    for k, v in params.items():
        if k in allowed and v is not None:
            parts.append(f"{k}={urllib.request.quote(str(v))}")
    return ("?" + "&".join(parts)) if parts else ""


def _handle_tool_call(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    args = arguments or {}

    if name == "list_projects":
        result = _api_get("/v1/agent/projects")

    elif name == "get_project_context":
        pid = args.get("project_id", "")
        if not pid:
            return {"content": [{"type": "text", "text": json.dumps({"ok": False, "error": "project_id is required"}, indent=2)}]}
        result = _api_get(f"/v1/agent/projects/{urllib.request.quote(pid)}/context")

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
        result = _api_get(f"/v1/agent/search?q={urllib.request.quote(q)}&limit={limit}")

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
                "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
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


def main():
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


if __name__ == "__main__":
    main()
