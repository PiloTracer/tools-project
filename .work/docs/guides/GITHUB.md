# GitHub Integration Guide

Link your project to GitHub repositories for automatic commit syncing and task linking.

## How it works

1. **Link a repo** — Add a GitHub repository URL and a personal access token (PAT).
2. **Background poll** — The system polls GitHub for new commits every N seconds (default 300, configurable per repo).
3. **Activity feed** — New commits appear in the project's activity feed.
4. **Task linking** — Commits containing task/ticket refs (e.g., `PROJ-123`) are automatically linked.

## Setup

### 1. Generate a GitHub PAT

Create a [fine-grained personal access token](https://github.com/settings/tokens) with:
- **Repository access:** Only the repos you want to link
- **Permissions:** `Contents` (read-only)

### 2. Link the repository

Navigate to **Project Settings → GitHub Repositories** and add:
```
https://github.com/your-org/your-repo
```
Paste your PAT and click "Link repository".

### 3. Verify

Commits will appear in:
- The **GitHub tab** (`/projects/[id]/github`) within one poll cycle
- The **Activity feed** as `github_commit` cards

## Per-Link Configuration

Each linked repo can have its own poll interval (click the interval in Settings to edit):

- Range: 60–86400 seconds (1 minute to 24 hours)
- Busy repos: sync every 60s
- Quiet repos: sync every hour

## Backfill

To pull in historical commits, use the "Re-sync GitHub" button in the activity feed. You can specify the number of days to go back (1–365).

## Token Health

The system automatically checks token validity every 5 minutes. A warning banner appears at the top of the project page if any token is invalid or expiring.

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| "Token rejected" (401) | PAT is invalid or expired. Generate a new one. |
| "Token lacks access" (403) | PAT doesn't have access to this repo. Check repo permissions. |
| "Repository not found" (404) | The URL is wrong or the repo is private without proper PAT. |
| No commits appearing | PAT may be invalid, or poll interval hasn't elapsed yet. |
| Sync shows errors | Check the sync status badge for error details. |
