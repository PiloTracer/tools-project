# Tutorial: read a ticket with its comments and screenshots

**Status: requires `agent_api_version 1.1.0` — implemented in the repository (SPEC amendment 01 P0), pending deployment.**
The routes and tools in this tutorial (`/v1/agent/tickets/{ticket}`, `…/activities`,
`/v1/agent/attachments/{id}`, and the MCP tools `get_ticket_detail`, `list_ticket_activities`,
`get_attachment`) do **not** exist on a `1.0.0` deployment; they return `404`. They are specified
and test-planned in
[`.work/features/agent-query-api/20261030-SPEC-amendment-01.md`](../../features/agent-query-api/20261030-SPEC-amendment-01.md).
Until that ships, an agent can only list the ticket and read its description (whose image links
require a browser session).

**Validation:** the contract was implemented and gated on 2026-10-30 (125 API tests incl. the
ticket-detail/attachment cases, live dev-stack check of detail + download headers); the deployed
instance still runs `0.1.3`, so re-run the commands there after deployment (amendment R22).

---

## Scenario

Another repository's agent receives: *"fix PZT-T-2 — documentos adjuntos fallidos"*, or a pasted URL
`https://project.cloudsys.win/projects/19b24527-…/tickets/<uuid>`.

The report says "we tested several competitions and they all failed". The failing HTTP state and the
button that was used exist only in the attached screenshot. A text-only API cannot resolve this
incident; this workflow can.

**Prerequisites:** the connection steps in
[`LLM-2-API_SETUP.md`](LLM-2-API_SETUP.md) (personal key in `~/.tools-project-key`, MCP registered,
`--self-check` green).

---

## Step 1 — resolve the ticket from a ref or a URL

`{ticket}` accepts the UUID **or** the ref (`PZT-T-2`), trimmed and case-insensitive.

```bash
BASE=$(grep '^BASE_URL=' ~/.tools-project-key | cut -d= -f2-); BASE=${BASE:-http://localhost:8300}
KEY=$(tail -n1 ~/.tools-project-key)
UA='User-Agent: tools-project-mcp/1.1.0'

# from a ref
curl -s -H "X-Api-Key: $KEY" -H "$UA" "$BASE/v1/agent/tickets/PZT-T-2" | head -c 400

# from a pasted URL: take the last path segment (the ticket UUID)
TICKET_URL='https://project.cloudsys.win/projects/<project-uuid>/tickets/<ticket-uuid>'
TICKET_ID=${TICKET_URL##*/}
curl -s -H "X-Api-Key: $KEY" -H "$UA" "$BASE/v1/agent/tickets/$TICKET_ID" | head -c 400
```

A web URL used with an API key answers `307 → /login`; the UUID inside it is what the API accepts.
(1.1.0 also returns `web_url`, so an agent can hand the human a working link.)

## Step 2 — read the ticket

```bash
curl -s -H "X-Api-Key: $KEY" -H "$UA" "$BASE/v1/agent/tickets/PZT-T-2" \
  | python3 -c '
import json,sys
t = json.load(sys.stdin)["data"]["ticket"]
print(t["ref"], "|", t["title"], "|", t["status"], "|", t["priority"])
print("queue:", t["queue_slug"], "requester:", t["requester_email"])
print("created:", t["created_at"], "first_response:", t["first_response_at"], "resolved:", t["resolved_at"])
print("counts:", t["counts"], "attachments truncated:", t["attachments_truncated"])
for a in t["attachments"]:
    print("  attachment:", a["filename"], a["mime"], a["size_bytes"], a["scope"], a["is_image"])
print(t["description_resolved"])'
```

What to look at, in order:

1. `description_resolved` — the report text with **working** image URLs. Use it for the narrative.
2. `attachments[]` — filename/mime/size/scope; `markdown_ref` tells you which ones the description
   embeds, and the array is ordered with those first.
3. `counts` — how many comments/attachments/commits to expect. If `attachments_truncated` is `true`,
   page nothing: description-referenced files are already included.
4. `reporter` / `assignee` / lifecycle timestamps — who reported it, who owns it, how long it has
   been open (`first_response_at`, `resolved_at`, `closed_at`).

MCP equivalent: `get_ticket_detail(ticket="PZT-T-2")` returns the same JSON as text.

## Step 3 — read the comment thread

The inline `activities` page is **newest first** (max 50 by default). For a chronological read, call
the activities route with `order=asc`:

```bash
curl -s -H "X-Api-Key: $KEY" -H "$UA" \
  "$BASE/v1/agent/tickets/PZT-T-2/activities?order=asc&limit=200" \
  | python3 -c '
import json, sys
d = json.load(sys.stdin)["data"]
print("total:", d["total"], "has_more:", d["has_more"])
for i in d["items"]:
    tag = "INTERNAL" if i["is_internal"] else i["kind"]
    who = (i["actor"] or {}).get("display_name", "-")
    print()
    print(i["created_at"], who, "(" + tag + ")")
    print(i["body"])
    for a in i["attachments"]:
        print("   file:", a["filename"], a["download_url"])'
```

Rules that matter when analysing an incident:

- `is_internal: true` entries are **staff-only**. A key owned by a client participant never
  receives them (nor their files).
- `meta_json` carries structured context — status transitions (`from`/`to`) and GitHub commit links
  are there; use it instead of re-parsing prose.
- `has_more` + `next_offset` page a long thread; `kind=` filters (e.g. `kind=status_change` to see
  the lifecycle alone).
- MCP equivalent: `list_ticket_activities(ticket="PZT-T-2", order="asc", limit=200)`.

## Step 4 — look at the screenshot

Two ways, same bytes.

**Through the MCP tool (preferred for an LLM):**

```
get_attachment(attachment_id="8b3cd170-7b4b-4170-a889-53e1dd22798a")
```

The tool returns an `image` block the model can see directly (images ≤ 5 MiB), a `text` block for
text files, or — for larger/other files — writes the file to
`~/.cache/tools-project/attachments/` and returns `{path, filename, mime, size_bytes, sha256}`.
A metadata block always accompanies it.

**Through curl (for scripts):**

```bash
curl -s -D /tmp/att.h -o /tmp/pzt-t-2.png \
  -H "X-Api-Key: $KEY" -H "$UA" \
  "$BASE/v1/agent/attachments/8b3cd170-7b4b-4170-a889-53e1dd22798a"
grep -iE 'content-(type|length|disposition)|x-content-type' /tmp/att.h
file /tmp/pzt-t-2.png          # PNG image data, …
```

`?download=1` switches `Content-Disposition` from `inline` to `attachment`. There is no range
support and no server-side OCR — the model reads the image.

## Step 5 — resolve the issue with the evidence

A workable agent loop for an incident like PZT-T-2:

1. **Reproduce with the facts from the ticket** — queue, environment, timestamps, the failing state
   visible in the screenshot, the comments that tried it since.
2. **Find the code** in the consuming repository (the ticket ref is the join key: commit subjects
   use `PZT-T-2: …`).
3. **Fix, test, commit** with `PZT-T-2: <plain-language subject>` — commit linking attaches it to the
   ticket automatically (default-branch sync, see [`REPO_INTEGRATION.md`](REPO_INTEGRATION.md)).
4. **Verify** the linked commit appears in `get_ticket_detail(...)` → `linked_commits[]`
   (`state: "resolved"` once synced, `"pending"` before).
5. **Report back** with the ref, the evidence you used, and the change — the API is read-only, so a
   status change or a customer comment remains a human action in the web UI.

## Step 6 — verify the workflow end to end

```bash
# 1. detail by ref
curl -s -H "X-Api-Key: $KEY" -H "$UA" "$BASE/v1/agent/tickets/PZT-T-2" \
  | python3 -c 'import json,sys; t=json.load(sys.stdin)["data"]["ticket"]; print(t["ref"], t["counts"], len(t["attachments"]))'
# expect: PZT-T-2 {'activities': <n>, 'attachments': 1, 'linked_commits': <n>} 1

# 2. thread
curl -s -H "X-Api-Key: $KEY" -H "$UA" "$BASE/v1/agent/tickets/PZT-T-2/activities?order=asc" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin)["data"]; print(len(d["items"]), d["total"])'
# expect: identical (no pagination needed) or items < total with has_more=true

# 3. bytes
curl -s -o /tmp/a.png -w '%{http_code} %{content_type}\n' -H "X-Api-Key: $KEY" -H "$UA" \
  "$BASE/v1/agent/attachments/8b3cd170-7b4b-4170-a889-53e1dd22798a"
# expect: 200 image/png

# 4. the MCP copy actually used by the agent
python3 .opencode/mcp/project-mcp/mcp_server.py --self-check
```

If any step returns `404`, the deployment is still `1.0.0` — stop and say so; do not substitute the
web UI and claim success.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `404 {"detail":"ticket_not_found"}` | Wrong ref/UUID, another tenant, or no access | Confirm the ref in the web UI; the API deliberately does not distinguish |
| `404` on the detail route | Deployment is `1.0.0` | Check `/openapi.json` `info.version` |
| `404 {"detail":"attachment_not_found"}` | Wrong id, file purged from disk, bad storage key, or internal note seen by a client | Re-read `attachments[]`; ask staff for internal notes |
| `403` HTML / `Error 1010` | Default urllib UA | Send `User-Agent: tools-project-mcp/<version>` |
| Image truncated in the model context | Larger than the 5 MiB inline cap | The tool saves it and returns the path — read the file, or raise `TOOLS_PROJECT_INLINE_IMAGE_MAX_BYTES` deliberately |
| Comments missing that exist in the UI | Client participant (internal notes hidden), or the API predates 1.1.0 | Check the caller's role; check the version |
| `web_url` is `null` | `PUBLIC_WEB_BASE_URL` not configured on the deployment | Use the URL from the ticket link you were given |

## See also

- [`../agent-query-api.md`](../agent-query-api.md) — contract, limits, errors
- [`LLM-2-API_SETUP.md`](LLM-2-API_SETUP.md) — connect the agent first
- [`REPO_INTEGRATION.md`](REPO_INTEGRATION.md) — commit linking, plan sync
- `20261030-SPEC-amendment-01.md` — R3/R6/R7/R9/R22 for the exact field and tool rules
