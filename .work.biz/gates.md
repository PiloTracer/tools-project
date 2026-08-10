# Gates — readiness ledger

Machine-readable record of which Business OS readiness states this project has reached.
Gated skills read this file in their I0 pre-check before doing any work.

## Schema

One `## <gate-id>` section per gate, each with the five fields below.

**Reading rule (tolerant on purpose, because real ledgers get annotated by hand):**

- A gate counts as met **only** when its `**Status:**` value *starts with* the word `PASS`.
  Trailing commentary is fine and encouraged: `**Status:** PASS 2026-07-25 - verified live
  (screenshots: dir/)` counts as met.
- Anything else means not met: `NOT MET`, `NOT ATTEMPTED`, `ACTIVATED`, `NONE`, `FAIL`,
  `BLOCKED`, a missing `Status` line, or a missing section.
- Gate ids match on a normalized form. `## active deal`, `## Active-Deal`, and
  `## active_deal` all resolve to `active-deal`. Prefer the hyphenated form in new files.
- Extra sections beyond the five gates are allowed. Projects often add their own, for
  example a proof-asset table. Nothing reads them as gates.

| Field | Meaning |
|-------|---------|
| `**Status:**` | `PASS` or `NOT MET` |
| `**Certified:**` | ISO date the gate was promoted, or `—` when not met |
| `**By:**` | The skill and verb allowed to promote this gate |
| `**Evidence:**` | Paths that prove the gate; checked by `scripts/gate-verify.sh` |
| `**Next gate:**` | What to work on next |

**Rules:**

- Only the skill named in `**By:**` may promote its gate to PASS.
- Never hand-edit a `Status` to PASS. Run the promoting skill so the evidence gets written too.
- A gate demotes to `NOT MET` when its evidence disappears or its upstream gate demotes.
- `scripts/gate-verify.sh` fails when a gate claims PASS without its evidence on disk.

---

## strategy-ready
**Status:** NOT MET
**Certified:** —
**By:** @biz-strategy certify
**Evidence:** `.work.biz/strategy/certification.md`
**Next gate:** brand-ready — run `@biz-brand audit` then `@biz-brand overhaul`

## brand-ready
**Status:** NOT MET
**Certified:** —
**By:** @biz-brand overhaul
**Evidence:** `.work.biz/reference/BRAND_STATUS.md`
**Next gate:** pipeline-ready — run `@biz-pricing set`, fill the pipeline tracker and outreach cadence, then `@biz-review status`

## pipeline-ready
**Status:** NOT MET
**Certified:** —
**By:** @biz-review status
**Evidence:** `.work.biz/strategy/pricing.md`, `.work.biz/pipeline/pipeline_tracker.md`, `.work.biz/pipeline/outreach-cadence.md`
**Next gate:** sales-ready — run `@biz-discovery prepare` then `@biz-discovery run`

## sales-ready
**Status:** NOT MET
**Certified:** —
**By:** @biz-discovery run
**Evidence:** `.work.biz/pipeline/pipeline_tracker.md` with at least one completed discovery call logged
**Next gate:** active-deal — run `@biz-discovery run` until a deal reaches Conversation stage or later

## active-deal
**Status:** NOT MET
**Certified:** —
**By:** @biz-discovery run
**Evidence:** `.work.biz/pipeline/pipeline_tracker.md` with at least one deal at Conversation stage or later
**Next gate:** none — active-deal is the final readiness state
