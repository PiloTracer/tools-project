# Delivery notes — tools-project (greenfield)

**Status:** Planning scaffold — replaces the previous “proveedores” estimate in this file. Not a commercial quote unless explicitly refreshed.

---

## 1. Vision

Deliver a **project management hub** (projects, components, tasks/TODOs, support tickets, rich activity, GitHub context) with **tools-dashboard OAuth** and a **Docker-first** repo layout comparable to **tools-rizervox**.

---

## 2. Phased roadmap (suggested)

| Phase | Focus |
|-------|--------|
| **0 — Foundations** | **Done (boilerplate):** Compose (`web`, `api`, `postgresql`), Next.js OAuth routes, FastAPI `/healthz` + stubs. Remaining: register real OAuth client + validate login E2E. |
| **1 — Core domain** | API + Postgres: projects, components, tasks; minimal list/detail UI; dashboard user identity from JWT/session as per org pattern. |
| **2 — Tickets & activity** | Support tickets, comments, attachments (S3/MinIO pattern if org standard), notifications (optional, SMTP or internal). |
| **3 — GitHub** | Repo linkage per project/component; commit log or webhook ingestion; rate limits and caching. |
| **4 — Hardening** | RBAC, audit fields, backup/runbook, staging/prod compose or K8s manifests per org standards. |

---

## 3. Architecture constraints

- **Single IdP:** tools-dashboard only.
- **No secrets in git;** `credentials/` and `.env` excluded.
- **Port discipline:** document host ports in `CONTEXT.md` and `.env.example`; avoid collisions with dashboard and rizervox.

---

## 4. Immediate engineering checklist

1. **E2E OAuth:** register client in tools-dashboard; confirm `/sign-in` → IdP → `/oauth/complete` → cookies with real secrets.
2. **ORM:** add SQLAlchemy 2 + Alembic (or org standard); first migration for `projects` / membership; connect `DATABASE_URL` in `api`.
3. **OpenAPI:** define `/v1/projects`, tasks, tickets CRUD; Bearer JWT validation aligned with dashboard tokens.
4. **Auth:** document `AUTH_*` for ops — standalone vs integrated vs hybrid; JWT hardening checklist.

---

## 5. Success criteria (MVP)

- User can sign in via dashboard OAuth and see a **project list** backed by the API.
- User can create/edit **tasks** and **tickets** with **activity** (text + at least one attachment path).
- **GitHub** shows **recent commits** for a linked repo on project or component detail.

---

*This document is internal planning for tools-project; update as scope is agreed with stakeholders.*
