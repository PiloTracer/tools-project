# I Replaced Four SaaS Tools With One Self-Hosted App. Here's What I Learned.

**Most tooling splits the whole picture across four windows you can never fit on one screen.**

> **Free, open source (MIT), self-hostable today:** <https://github.com/PiloTracer/tools-project>

A prospect becomes a client in the CRM. Engineering picks up the work in the task tracker. A bug gets filed as a ticket. The commit that fixes it sits in GitHub with a vague message. Six weeks later someone asks how we shipped that feature for Umbrella Corp — and nobody can answer in under twenty minutes.

I built **tools-project** to close that gap.

One self-hosted app. One login. One activity feed that tells the truth across sales and delivery. No SaaS seats. No data leaving your infrastructure.

## What it does

- **Projects, tasks, tickets, attachments.** Kanban, ticket triage, threaded comments, @mentions. Attach any file to any ticket, task, or comment.
- **CRM that connects to the work.** A nine-stage prospect pipeline. One-click prospect-to-client promotion. Client contacts with access roles. A client portal stakeholders can log into — seeing only the projects they've been granted, never internal discussions or members.
- **GitHub, connected.** Link multiple repositories per project (tokens encrypted). New commits surface in the activity feed, and any cached commit can be cited from inside a comment.

## The part that surprised me most

Commits get linked to tasks automatically — **including when an AI agent does the coding**. Each task has a short reference like `PROJ-456`. A small git hook prepends that ref to the commit subject so every commit carries the work it belongs to. The moment it lands in `main`, the right task lights up.

It works the same way for a human typing `git commit` and for an AI coding agent running it programmatically. This whole project was built using three companion agent-orchestration frameworks (`.ai`, `.ai.ui`, `.ai.biz`) that produce exactly that kind of structured, ref-linked work — so the convention is enforced at the commit layer, not bolted on after.

## Built for

- **Founders and small consultancies** paying for a tracker, a CRM, and a wiki — and wanting one bill, one login.
- **Engineering teams that sell** — where sales and delivery share staff, so tools should share a brain.
- **Teams starting to use AI coding agents seriously.**

## Honest about what this is

A **first draft**. v0.1.2 is the first public-release tag, not the finish line. I am going to keep improving it consistently and regularly — webhooks, email, mobile surfaces, reporting dashboards are next. No webhooks yet (polling at 5 minutes is enough). No email yet (inbox is in-app). No mobile app (web is responsive — I won't call it more than that).

Rather ship honest v0.1.2 than pretend v1.0.

## Try it

**Repository (free, MIT, public):** <https://github.com/PiloTracer/tools-project>  
**Live partial demo (viewer permissions, read-only):** <https://logicbison.com/work/tools-project-hub> — URL and credentials are on that page.

If you build something with it — or break something with it — I want to hear about it.

---

*#SelfHosted #ProjectManagement #CRM #DeveloperTools #OpenSource #MITLicense*