# Brand Status

**Purpose:** Persistent record of brand audit results and overhaul dates. `@biz-brand status` reads this file; `@biz-brand audit` and `@biz-brand overhaul` write it. It is the evidence for the `brand-ready` gate.

**Last updated:** <date>

## Audit history

| Date | LinkedIn | Website | Brand assets | YouTube | Overall | Verdict |
|------|----------|---------|--------------|---------|---------|---------|

Scores are `passed/total` per the check tables in `skills/biz-brand/skill.md` § 1. Verdict is `overhaul needed` or `brand-ready`.

## Overhaul log

| Date | Scope | 5-second test | Notes |
|------|-------|---------------|-------|

Scope is which surfaces were rewritten (LinkedIn, website, brand assets, YouTube). The 5-second test result is `pass` or `fail` per § 4; a `fail` blocks the `brand-ready` gate.

## Current surfaces

| Surface | State | Last changed |
|---------|-------|--------------|
| LinkedIn headline | | |
| LinkedIn About | | |
| LinkedIn Featured (3 items) | | |
| LinkedIn banner | | |
| Website homepage | | |
| Website Calendly + analytics | | |
| Brand assets (colors, type, tone) | | |
| YouTube channel (if active) | | |

## What to do after an overhaul

1. Append a row to **Overhaul log** with the date, scope, and 5-second test result.
2. Refresh **Current surfaces** so `@biz-brand status` reports the truth.
3. Promote `brand-ready` in `.work.biz/gates.md` only when every § 7 success criterion is met.
4. Update `context/HANDOFF.md` and `plans/NEXT.md`.
