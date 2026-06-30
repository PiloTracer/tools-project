# I Replaced Four SaaS Tools With One Self-Hosted App. Here's What I Learned.

**A project manager's job is to see the whole picture. Most tooling splits it into four windows you can never fit on one screen.**

> **Free, open source (MIT), self-hostable today:** <https://github.com/PiloTracer/tools-project>

---

I have spent enough time watching teams lose context to know the pattern. A prospect becomes a client in the CRM. Engineering picks up the work in the task tracker. A bug gets filed as a support ticket. The commit that fixes it sits in GitHub with a vague message. Six weeks later someone asks: "How did we end up shipping that feature for Umbrella Corp?" — and nobody can answer in under twenty minutes.

So I built **tools-project**. It is one self-hosted application that combines project tracking, support tickets, a CRM sales pipeline, and GitHub integration — running in a single Docker Compose stack on a machine you control. No SaaS seats. No data leaving your infrastructure. One URL, one login, one activity feed that actually tells the truth about what is happening across sales and delivery.

This is what I want to walk you through — and the non-obvious part at the end that made it possible.

## What is actually in the box

**Project management without the spreadsheet fatigue.** Each project gets a short key — `PROJ`, `UMB`, `TPR` — and every task and ticket inside it gets a human-readable reference generated from that key: `PROJ-123`, `UMB-T-7`. You can drag tasks across a Kanban board with four standard columns, file support tickets against a triage queue, break work into components, and watch a single threaded activity feed per project where @mentions, system events, and commit cards all show up in chronological order. Mentions hit a centralized inbox. Watches let you follow a specific task without being assigned to it.

**A CRM pipeline that connects to the work, not just the sales team.** Prospects move through nine stages — `target → connected → engaged → call scheduled → call done → proposal sent → negotiating → won` / `lost` — with validated transitions so nobody skips from "connected" straight to "won" by accident. When a deal closes, you promote the prospect to a client record in one click. From there you add contacts per company, link that client to the project you are about to deliver, and grant each contact a role: *view*, *contribute*, *decision-maker*, or *billing*. A client stakeholder gets a separate login — a portal — where they only see the tasks and public activity on the projects they have been granted access to. Internal discussions, members, GitHub, and settings stay hidden.

**Attach anything to anything.** This was a deliberate choice and one of the features I am proudest of. Upload a screenshot to a ticket. Drop a PDF contract on a task. Paste a log file onto an activity reply. Files are content-type sniffed on the server (so a `.txt` renamed `.png` is still treated as text), capped per file at 25 MiB, capped per project by file count and total bytes you can configure, and aged out automatically on a retention schedule. No more "where did that screenshot go?" — it lives next to the thing it was about.

**GitHub integration that respects how engineers actually work.** You link any number of repositories to a project using a personal access token. Tokens are encrypted at rest with Fernet symmetric encryption — never returned by any API, never written to logs. A background poller pulls new commits on a configurable interval (five minutes by default), caches them in the database with the full `html_url` GitHub returns, and surfaces each new commit as an activity card with a clickable SHA, repo, and preview. A backfill action re-syncs the last 365 days. A commit picker lets you cite any cached commit from inside a comment or reply, and a search-as-you-type modal finds it by message or SHA. Verification still happens on GitHub — we link out, we do not try to render diffs in-app.

## The part I did not expect to matter this much

Here is the honest surprise. The single most useful feature in tools-project — the one I would build first if I started over — is that **commits get linked to tasks automatically, including when an AI agent does the coding.**

It works because of a small piece of plumbing and a design choice most teams skip:

1. Every task and ticket has a structured ref like `PROJ-456` or `PROJ-T-23`.
2. A `prepare-commit-msg` git hook reads the current branch name (or a session file written at session start) and prepends the active ref to the commit subject before the commit is created. If you are on `feature/PROJ-456-login-form`, your commit becomes `PROJ-456: Add login form with email validation` — automatically, no matter who or what is typing the commit.
3. When the GitHub poller pulls that commit back into the app, a normalizer parses the subject line, extracts the ref, and writes a row into a `commit_subject_refs` table that links the commit to the task.

The result is that the moment work lands in `main`, the relevant task lights up with a linked commit — a clickable SHA you can open on GitHub. The engineering team does not have to remember to paste Jira links into PR descriptions. They do not have to do anything. The convention is enforced at the `git commit` layer, which means it works for a human typing `git commit -m` and it works identically for an AI coding agent running `git commit` programmatically.

That last point matters more than it sounds. I built tools-project using three companion agent-orchestration frameworks — `.ai` (Agent OS), `.ai.ui` (UI Design OS), and `.ai.biz` (Business OS). They live alongside the repo as `.cursorrules`-driven skill directories that plan, spec, implement, and verify work in structured milestones. Every commit an AI agent makes in a session flows through the same hook, gets the same ref prefix, and lands in the same auto-association pipeline. The "AI-built this feature" commit and the "human fixed this typo" commit are indistinguishable from the project manager's point of view — both show up on the right task.

I did not set out to build an "AI-native" project tool. I set out to stop losing context between tools, and the same machinery that solves the CRM-engineering gap happens to solve the agent-human gap too.

## The stack, in case you wanted to know

- **Frontend:** Next.js 16 with the App Router, React 19 server components, TypeScript. Styling is token-driven so a brand refresh is one file.
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2 in async mode, `asyncpg` driver. Structured logging, an `X-Request-Id` header on every response, a `/healthz` endpoint that pings the database.
- **Database:** PostgreSQL 16. One database, no caching layer. Schema changes are plain idempotent SQL scripts with `IF NOT EXISTS` clauses — no Alembic, no migration tooling to learn. Re-running them on every cold start is a feature, not a bug.
- **Auth:** Dual-mode by design. Local email/password with bcrypt and JWT for standalone deployments, or OAuth 2.0 with PKCE for an existing identity provider. Both can run simultaneously for gradual migration.
- **Containers:** Docker Compose, with split dev and production profiles. Cold start of a fresh stack — Postgres, API, frontend — runs in one `docker compose --profile dev up --build`.

The whole thing fits on a single small VPS for v0.1.0. Most teams will not need anything bigger for a long time.

## Who this is for

- **Small consultancies and agencies** who currently pay for a task tracker, a CRM, and a GitHub-friendly wiki and would like one bill and one login instead.
- **Engineering teams that sell** — anyone where the sales motion and the delivery motion have to share a brain because they share staff.
- **People who want to host their own project data** for legal, contractual, or simply philosophical reasons — your clients, your code, your prospects, your server.
- **Teams starting to use AI coding agents seriously** — because the moment an agent can run `git commit`, you need commit messages that auto-link to tracked work. This project was built with that being the default, not the afterthought.

## What is deliberately not here

No webhooks for GitHub yet — polling at a five-minute default is good enough for v0.1.x, and webhooks add an ingress surface I did not want to design in a hurry. No email notifications yet — the inbox is in-app. No mobile app — the web UI is responsive, but I will not lie and call it a mobile experience. These are the next three things on the roadmap, in roughly that order.

I would rather ship honest v0.1.x than pretend v1.0.

## One honest disclaimer: this is a first draft

Everything above is real, working code you can clone and run today. It is also a **first draft**. v0.1.2 is the first public-release tag, not the finish line.

I am going to keep improving this consistently and regularly — fixing what breaks, sharpening what is rough, and adding the features a project management hub with integrated CRM genuinely needs: webhooks for instant GitHub updates, email and calendar notifications, mobile-friendly surfaces, reporting dashboards, richer onboarding checklists, an OpenAPI-first plugin system. The roadmap is not aspirational marketing; it is the next list of pull requests.

If that is the kind of tool you want to grow with rather than inherit finished, this is a good moment to start.

## If you want to look at it

**The repository is free, open source (MIT), and public:** <https://github.com/PiloTracer/tools-project>

It contains the full source, a quick start that gets you logged in in under a minute, four guides (auth, GitHub, CRM, admin), two step-by-step tutorials, and three reference documents covering every environment variable, every Docker command, and every REST endpoint. The release notes are in the repo root `CHANGELOG.md`. Clone it, run it, break it, open issues.

**Want to see it before you clone it?** A live partial demo (limited viewer permissions — read-only, so you can click around without breaking anything) is running at <https://logicbison.com/work/tools-project-hub>. The URL and credentials are listed on that page.

If you build something with it — or break something with it — I want to hear about it.

---

*#SelfHosted #ProjectManagement #CRM #DeveloperTools #OpenSource #MITLicense*