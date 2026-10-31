#!/usr/bin/env bash
# Keep the consumer copy of the MCP server in sync with the packaged canonical file.
#
# Usage:
#   bin/mcp-sync.sh check   # exit 1 when the repo copy drifts (CI / pre-commit)
#   bin/mcp-sync.sh sync    # copy the canonical file into .opencode/…
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/api/app/client/mcp_server.py"
DST="$ROOT/.opencode/mcp/project-mcp/mcp_server.py"

case "${1:-check}" in
  check)
    [[ -f "$SRC" && -f "$DST" ]] || { echo "mcp-sync: missing source or copy" >&2; exit 2; }
    if cmp -s "$SRC" "$DST"; then
      echo "mcp-sync: ok ($(grep -c 'User-Agent' "$DST") UA header reference(s))"
    else
      echo "mcp-sync: drift — run bin/mcp-sync.sh sync" >&2
      exit 1
    fi
    ;;
  sync)
    mkdir -p "$(dirname "$DST")"
    cp "$SRC" "$DST"
    chmod 755 "$DST"
    echo "mcp-sync: copied $(basename "$SRC") → ${DST#"$ROOT"/}"
    ;;
  *)
    echo "usage: bin/mcp-sync.sh [check|sync]" >&2
    exit 2
    ;;
esac
