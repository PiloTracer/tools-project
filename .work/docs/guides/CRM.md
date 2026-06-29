# CRM Pipeline Guide

Track sales leads from initial contact through to client onboarding.

## Pipeline Stages

```
target → connected → engaged → call_scheduled → call_done → proposal_sent → negotiating → won / lost
```

| Stage | Meaning |
|-------|---------|
| target | Initial lead identified |
| connected | First contact established |
| engaged | Active conversation in progress |
| call_scheduled | Meeting or call booked |
| call_done | Call completed |
| proposal_sent | Proposal or quote delivered |
| negotiating | Terms being discussed |
| won | Deal closed → promotes to Client |
| lost | Deal lost (terminal — cannot transition out) |

## Working with Prospects

### Creating a prospect

From the **Prospects** page, click "Add prospect" and fill in:
- Company name (required)
- Pipeline stage (defaults to "target")
- Pipeline value (optional, for deal tracking)
- Source (how they were referred)
- Notes

### Moving through stages

1. Open a prospect's detail page.
2. The current stage is shown prominently at the top.
3. Click "Advance stage" to move forward through the pipeline.
4. Terminal stages (`won`, `lost`) cannot be changed.

### Converting to client

When a prospect reaches **won**:
1. Click "Promote to client" (visible only at the `won` stage, only if not already a client).
2. A client record is auto-created with the company name.
3. A success dialog offers a direct link to the new client page.
4. The prospect's `client_id` field now links to the client record.

## Managing Clients

### Client companies

Each client has:
- **Name** and **slug** (auto-generated for URL identification)
- **Industry** classification
- **Notes** for account information
- Linked **contacts** (people at the company)
- Linked **projects** (work being done for them)

### Client contacts

Add contacts to a client record:
- **Name, email, phone** — contact information
- **Role** — `contact` or `contact_admin`
- **Primary** — mark one contact as the primary point of contact
- **User account** — optionally link to a system user for client portal access

### Granting project access

1. Navigate to **Project Settings → Client Access**.
2. Grant access to specific client contacts with a role:
   - `view` — Read-only access to tasks and public activity
   - `contribute` — Can create and edit assigned items
   - `decision_maker` — Elevated permissions within the project
   - `billing` — Access to billing-related information

### Client portal

Client stakeholders log in at `/client/login` and see:
- A dashboard listing projects they have access to
- Project view with assigned tasks and public activity
- **No access** to: internal activity, project settings, GitHub, members, or admin features

Client participants see content from **all contacts in their company** (company-scoped visibility, FR-5).
