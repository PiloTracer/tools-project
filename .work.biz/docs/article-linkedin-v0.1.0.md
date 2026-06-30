# I Replaced Four SaaS Tools With One Self-Hosted App. Here's What I Learned.

**Most tooling splits the whole picture across four windows you can never fit on one screen.**

> **Free, open source (MIT), self-hostable today:** <https://github.com/PiloTracer/tools-project>

---

A prospect becomes a client in the CRM. Engineering picks up the work in the task tracker. A bug gets filed as a ticket. The commit that fixes it sits in GitHub with a vague message. Six weeks later someone asks how we shipped that feature for Umbrella Corp — and nobody can answer in under twenty minutes.

I built **tools-project** to close that gap: one self-hosted app, one Docker Compose stack, one login, one activity feed that tells the truth across sales and delivery. No SaaS seats, no data leaving your infrastructure.

## Four pillars, one app

**1. Project management.** Each project gets a short key (`PROJ`, `UMB`), and every task and ticket gets a human-readable ref like `PROJ-123` or `UMB-T-7`. Kanban boards, a support-ticket triage queue, threaded activity feed with @mentions, components, inbox, watches — the work-tracking layer, with refs that travel everywhere else.

**2. CRM pipeline that connects to the work, not just the sales team.** Prospects move through nine validated stages — `target → connected → engaged → call scheduled → call done → proposal sent → negotiating → won/lost`. On `won`, promote the prospect to a client in one click. Add contacts, link that client to the project you are about to deliver, grant each contact a role (*view*, *contribute*, *decision-maker*, *billing*). A client stakeholder gets a portal login and sees only the tasks and public activity on the projects they have been granted access to — internal discussions, members, GitHub, and settings stay hidden.

**3. Attach anything to any ticket or task.** Screenshot on a ticket. PDF contract on a task. Log file on an activity reply. Files are content-sniffed server-side (a renamed `.png` is still treated as text), capped per file at 25 MiB, capped per project by count and total bytes you configure, and aged out automatically. The file lives next to the thing it was about.

**4. GitHub integration — and the part I did not expect to matter this much.** You link any number of repositories per project. PATs are encrypted at rest with Fernet, never returned by any API or written to logs. A background poller caches each commit with its `html_url`, surfaces commits as activity cards, and lets you cite any cached commit from a comment via a search-as-you-type picker. And — this is the headline — **commits get linked to tasks automatically, including when an AI agent does the coding.**

## The byte-sized version of how that auto-association works

1. Every task/ticket has a structured ref like `PROJ-456`.
2. A `prepare-commit-msg` git hook reads the branch name and prepends the ref to the commit subject automatically — so a commit on `feature/PROJ-456-login-form` becomes `PROJ-456: Add login form` before anyone types a message.
3. When the GitHub poller pulls the commit back in, a normalizer parses the subject and writes a row into `commit_subject_refs` linking the commit to the task.

The convention lives at the `git commit` layer, which means it works identically for a human typing `git commit -m` and for an AI coding agent running `git commit` programmatically. I built this app using three companion frameworks — `.ai` (Agent OS), `.ai.ui` (UI Design OS), `.ai.biz` (Business OS) — and every AI-agent commit flows through the same hook and lands on the right task. The "AI built this feature" commit and the "human fixed this typo" commit are indistinguishable from a project manager's point of view. I did not set out to build an "AI-native" tool — the same machinery that closes the CRM-engineering gap happens to close the agent-human gap too.

## The stack, in one breath

Next.js 16 + React 19 + TypeScript out front · Python 3.11 + FastAPI + SQLAlchemy 2 async + asyncpg out back · PostgreSQL 16 (no cache layer) · dual auth (local JWT **or** OAuth 2.0 + PKCE, both at once) · idempotent SQL scripts (no Alembic) · Docker Compose dev + production profiles. One small VPS is enough.

## Who it is for

Consultancies and agencies paying for a tracker, a CRM, and a GitHub-friendly wiki and wanting one bill. Engineering teams that sell — where sales and delivery share staff. Anyone hosting their own data for legal, contractual, or philosophical reasons. Teams starting to use AI coding agents seriously.

## Honest about what this is

This is a **first draft**. v0.1.2 is the first public-release tag, not the finish line. I am going to keep improving it consistently and regularly — webhooks for instant GitHub updates, email and calendar notifications, mobile-friendly surfaces, reporting dashboards — the roadmap is the next list of pull requests, not aspirational marketing. No webhooks yet (polling at 5 min is enough for v0.1.x), no email notifications (inbox is in-app), no mobile app (web is responsive — I will not call it more than that).

I would rather ship honest v0.1.2 than pretend v1.0.

## Try it

**Repository (free, MIT, public):** <https://github.com/PiloTracer/tools-project>  
**Live partial demo (viewer permissions, read-only):** <https://logicbison.com/work/tools-project-hub> — URL and credentials are on that page.

The repo contains a quick start that gets you logged in under a minute, four guides (auth, GitHub, CRM, admin), two tutorials, and three reference docs covering every env var, every Docker command, and every REST endpoint. Clone it, run it, break it, open issues.

If you build something with it — or break something with it — I want to hear about it.

---

*#SelfHosted #ProjectManagement #CRM #DeveloperTools #OpenSource #MITLicense*