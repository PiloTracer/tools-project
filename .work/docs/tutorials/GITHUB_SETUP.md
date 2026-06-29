# Tutorial: Connect a GitHub Repository

Link your project to a GitHub repo for automatic commit syncing.

## Prerequisites

- A project in tools-project
- A GitHub repository you own or have admin access to
- A GitHub personal access token (PAT) with `Contents: read` permission

## Step 1: Generate a GitHub PAT

1. Go to https://github.com/settings/tokens and click **Generate new token → Fine-grained token**.
2. Set:
   - **Token name:** "tools-project"
   - **Repository access:** "Only select repositories"
   - Select the repo you want to link
   - **Permissions → Contents:** "Read-only"
3. Click **Generate token** and copy the token value.

## Step 2: Link the repository

1. In tools-project, open your project.
2. Go to **Settings → GitHub Repositories**.
3. Under "Link repository", paste:
   - **GitHub repo URL:** `https://github.com/your-org/your-repo`
   - **Personal Access Token:** `github_pat_...`
4. Click **Link repository**.

The system immediately syncs the repo and fetches recent commits.

## Step 3: Browse commits

1. Go to the **GitHub** tab in your project.
2. You'll see:
   - **Linked Repositories** table: shows your repo, sync status, last sync time.
   - **Recent Commits** table: commit SHA, message preview, author, timestamp.
3. Click a commit SHA to open it on GitHub.
4. Use "Load more commits" to browse the full history.

## Step 4: See commits in activity

Commits appear in the **Activity** feed as automatic posts. Each shows:
- Short SHA
- Repository name
- First line of the commit message
- "Open on GitHub" link

## Step 5: Configure sync frequency

1. In **Settings → GitHub Repositories**, click the poll interval number (default `300s`).
2. Enter a new value (e.g., `60` for every minute, `3600` for every hour).
3. Click **Save**.

## Step 6: Link commits to tasks

If your commit messages contain refs like `MFP-123`, the system automatically:
1. Detects the ref in the commit message.
2. Creates a link between the commit and the task/ticket.
3. Shows "Linked" on the commit card and task detail page.

To enable this, ensure your project has:
- **Project key** set (Settings → Project Key)
- **Task registry** enabled (Settings → GitHub → Task Registry)
- **Auto-prefix** enabled (Settings → GitHub → Auto-Prefix)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Token rejected" | The PAT is invalid. Generate a new one and update it in Settings. |
| No commits after linking | Wait for the next poll cycle (default 5 min) or click "Sync now". |
| `html_url` missing | The sync derives the URL; if the GitHub API doesn't return one, it's constructed from owner/repo/sha. |
