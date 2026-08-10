# Content Status

**Purpose:** Single source of truth for what content is published, ready, blocked, or held. Read at session start. Do not recommend publishing anything marked `published`.

**Last updated:** <date>

## Summary

| Content type | Total | Published | Ready | Blocked | Hold |
|--------------|-------|-----------|-------|---------|------|

## By platform

Cross-platform index. Per-platform performance belongs in `pipeline/<platform>-tracker.md`, not here.

| Platform | Role in channel plan | Published | Last publish | Tracker file | Conversations produced |
|----------|---------------------|-----------|--------------|--------------|------------------------|

`Role in channel plan` must match `strategy/channel-plan.md`. If a platform has published items but no role, mark it **`not sanctioned`** and resolve the drift: either amend the channel plan or stop publishing there. A platform with published items and zero conversations is producing authority, not pipeline. Record that honestly rather than leaving the column blank.

## Items

| # | Piece | Status | Published | Platform / URL | Note |
|---|-------|--------|-----------|----------------|------|

## What to do after a publish

1. Update this file with the publish date and platform, and refresh the **By platform** row.
2. Append the piece to `pipeline/<platform>-tracker.md`. Create it from `templates/work/pipeline/platform-tracker.md.template` if this is the first publish on that platform.
3. Update `plans/NEXT.md` - remove the completed item, reorder what is left.
4. Update `context/HANDOFF.md` - log the publish.
5. Update `pipeline/pipeline_tracker.md` weekly metrics if it is the same week.
6. If the piece produced a conversation, log it in the tracker's conversations table. That column is the only one that connects content to revenue.
