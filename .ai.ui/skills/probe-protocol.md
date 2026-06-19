# Probe protocol (shared engine)

**Single source of truth** for the adaptive, gap-driven interrogation loop used by `probe` modes. `ui-design-foundation` and `ui-component-build` **reference** this file; they do not restate the loop. Each caller supplies a **coverage profile** (dimensions + exit gate + ledger path); this file owns the engine.

Not a skill folder — a shared engine doc (does not count as a skill).

## When to probe

Use `probe` when understanding is thin: vague brand/users, unclear archetype, no measurable craft target, unscheduled screens, ownerless design risks. The goal is to **interrogate until the agent can defend its readiness claim**, not to guess.

## The loop

One pass = **one probe iteration**:

```text
ASSESS → PRIORITIZE → ASK (≤5 targeted questions) → RECORD → RE-SCORE → EXIT?
```

1. **ASSESS** — score each dimension in the caller's coverage map: status `confirmed | partial | unknown`, confidence `high | med | low`, with cited evidence.
2. **PRIORITIZE** — target gate-blocking (★) dimensions that are `unknown`/`low` first.
3. **ASK** — ≤5 specific, answerable questions in one batch. No essays; offer options when it speeds the human up.
4. **RECORD** — write answers into the canonical artifacts (foundation docs, screen map, registries) **and** update the ledger. Set `confirmed/high` **only** with a cited source or a same-session owner answer; an inference is `partial/med` at best.
5. **RE-SCORE** — recompute Coverage; log the iteration.
6. **EXIT?** — stop when Coverage ≥ target **and** no ★ dimension is below `partial`. Otherwise carry open probes to the next pass. Owner-blocked items → `UNKNOWNS.md` (do not invent answers).

## Coverage Score

```text
Coverage = ( Σ weight×conf ) / Σ weight
conf: high=1.0  med=0.5  low=0.0      weight: gate-blocking(★)=2  else=1
```

Target defaults to **85%**. A ★ dimension still `unknown` blocks the exit gate regardless of the percentage.

## Ledger

Persist state in the caller's ledger (`PROBE_LEDGER.md`) so a probe is resumable and auditable. Template: [`templates/work.ui/plans/foundation/PROBE_LEDGER.md.template`](../templates/work.ui/plans/foundation/PROBE_LEDGER.md.template). Honesty rules are machine-checked by [`scripts/readiness-verify.sh`](../scripts/readiness-verify.sh).

## Ease-of-use rules

- **Never** dump the whole coverage map at the user — ask only what's blocking.
- ≤5 questions per pass; batch them; accept "skip / defer" → ledger Deferred.
- A probe must always end with a clear next action: continue, certify, or a named blocker.
- `probe - status` reports the ledger read-only; `probe - until ready` loops without re-prompting for confirmation between passes.
