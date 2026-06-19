# Guide — probe & free-text intake

Two ease-of-use entry points sit in front of the gated UI flow. Both let a human start from plain English; both keep the guardrails.

| You want… | Run | What it guarantees |
|-----------|-----|--------------------|
| The agent to **ask until it understands** the UI before committing to a foundation | `@ui-design-foundation probe` | Coverage ≥ 85% across fixed dimensions; no gate-blocking gap left silent |
| To **toss an idea** without knowing where it belongs | `@ui-screen-spec intake - <sentence>` | Classified, routed to one command, recorded so nothing is lost |
| To check the **roadmap is complete** before broad build | `@ui-component-build probe` | Every screen scheduled; primitives ordered first |
| A **read-only audit** of all of the above | `@ui-plan-verify audit` | Runs the verifiers, reports coverage + orphans, routes each gap |

## Probe — interrogate until ready

Engine: [`../../skills/probe-protocol.md`](../../skills/probe-protocol.md). One pass = `ASSESS → PRIORITIZE → ASK (≤5) → RECORD → RE-SCORE → EXIT?`.

- It scores each dimension (`confirmed/partial/unknown` × `high/med/low`), asks only what's blocking, and records answers into the foundation docs / screen map — not just the ledger.
- **Honesty is enforced:** a dimension may only be `confirmed/high` with a cited source or a same-session owner answer; `scripts/readiness-verify.sh` fails the ledger otherwise.
- Sub-modes: `probe - status` (read the ledger, ask nothing) · `probe - until ready` (loop passes without re-confirming between them).
- Owner-blocked answers go to `UNKNOWNS.md` — the agent never invents them.

Typical loop:

```text
@ui-design-foundation probe          # asks ≤5 questions, records, re-scores
@ui-design-foundation probe - status # see coverage + open probes any time
@ui-design-foundation certify screen-spec-ready
```

## Intake — the free-text front door

`@ui-screen-spec intake - <one sentence>` classifies by blast radius (first match wins): **brownfield** (no foundation yet) · **underspecified** (vague, no measurable outcome) · **cross-cutting** (new tokens/primitives/many screens) · **local** (one screen, existing tokens). Only `local` proceeds into `create`.

- Override the class with `; force=<class>`.
- Every request is appended to `NEXT_UI.md` § Intake queue, so a deferred idea is never dropped.
- Prompt examples (good vs wrong): [`../../skills/ui-screen-spec/reference.md`](../../skills/ui-screen-spec/reference.md).

## How they fit the readiness chain

```text
intake ─┬─ brownfield ────► @ui-design-foundation greenfield ─► probe ─► certify (screen-spec-ready)
        ├─ underspecified ► @ui-design-foundation probe ──────────────────┘
        ├─ cross-cutting ─► @ui-design-system init / tokens ─► plan
        └─ local ─────────► @ui-screen-spec create ─► @ui-component-build plan/start
```

Audit anytime with `@ui-plan-verify audit`. Verifier source of truth: `scripts/{framework,readiness,traceability}-verify.sh`.
