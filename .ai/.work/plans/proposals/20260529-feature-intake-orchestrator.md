# Proposal - free-text feature-intake orchestrator

**Status:** Accepted - implemented 2026-05-29 · **Owner:** framework maintainers · **Date:** 2026-05-29
**Decision:** approved. Implemented as an `intake` **mode on `feature-spec`** (no new skill). Open question resolved: the intake log reuses **`NEXT.md § Intake queue`** (lean default). Canonical classification table lives in `feature-spec/skill.md § Intake protocol` (kept with the protocol for self-containment, rather than `reference.md` as originally sketched). The framework-verify check is a **structural contract guard** (asserts all 4 classes + the `force=` override survive) - there is no executable classifier to behavior-test.

---

## 1. Problem

A user's most natural way to ask for work is one unstructured sentence: *"let users export invoices to CSV"*, *"make the dashboard load faster"*, *"add SSO"*. Today the framework can **accept** that text in two places (the `feature-request` routing bucket and free-text `@feature-spec create -`), but there is **no single front door that classifies the request and picks the right artifact**. The operator still has to know whether a sentence becomes a SPEC, a master-plan revision, or a brownfield alignment pass. That decision is exactly the knowledge a newcomer lacks.

## 2. Goal / non-goals

**Goal:** one entry point - `@feature-spec intake - <free sentence>` - that (a) classifies the request by blast radius, (b) routes to the already-existing executor, and (c) records the request so nothing is silently dropped. Deterministic, lean, no new artifact types.

**Non-goals:** implementing the feature; estimation/sizing in story points; replacing `probe`, `plan-repair`, or `feature-spec create`. It *dispatches* to those, it does not duplicate them.

## 3. Proposed design (lean - no new skill)

Add an **`intake` mode to the existing `feature-spec` skill**. Rationale: a 15th skill folder would grow the registry for pure routing logic that already lives next to `feature-spec create`. The orchestrator is ~30 lines of decision protocol, not a new domain.

Flow (one pass, deterministic):

```text
CLASSIFY (blast radius) → ROUTE (existing executor) → RECORD (request never lost)
```

**Classification table (the whole contract):**

| Signal in the request | Class | Routes to |
|-----------------------|-------|-----------|
| Single surface/endpoint/screen, no new cross-cutting NFR | **local** | `@feature-spec create - <free-text>` (CR0.5 derives slug) |
| Touches ≥2 milestones, new NFR target, or shifts scope | **cross-cutting** | `@plan-master probe` → `@plan-master revise` / `@plan-repair master - <goal>` |
| Repo has no foundation/master plan yet | **brownfield** | `@plan-verify brownfield` → `@plan-repair brownfield`, *then* re-run intake |
| Vague intent / no measurable outcome | **underspecified** | `@plan-foundation probe` (or `@plan-master probe`) until the outcome is stateable, then re-classify |

**RECORD step:** every intake appends a one-line entry to the request log (reuse `{PLANS_ROOT}/NEXT.md` § intake queue, or `UNKNOWNS.md` when deferred) so a request is auditable even when the operator stops before executing. No new file type.

## 4. Interface

```text
@feature-spec intake - <free sentence>     # classify + route + record
@feature-spec intake - <sentence> ; force=local   # operator overrides the class
```

Output is a short verdict: detected class, the one command to run next, and the recorded log line. The operator confirms or overrides; the orchestrator does not auto-execute cross-cutting/brownfield paths (those have their own gates).

## 5. Verification

- Self-contained: classification is a table lookup, so a `framework-verify` self-test can feed 4 canned sentences and assert the chosen class (cheap, no real plan needed).
- No traceability/readiness regression: intake only *dispatches*; the downstream gates (`probe`, `integrity`, `traceability-verify`) remain the source of truth.

## 6. Risks & open questions

| Risk / question | Note |
|-----------------|------|
| Misclassification of an ambiguous sentence | Mitigated by the `underspecified → probe` default and the `force=` override; never auto-executes destructive paths. |
| Mode bloat on `feature-spec` | Acceptable: 1 mode vs 1 new skill. Revisit only if intake logic outgrows ~1 screen. |
| Where the request log lives | **Open** - `NEXT.md § intake queue` (visible in the iteration carrier) vs a dedicated `intake.md`. Lean default: reuse `NEXT.md`. |
| Overlap with `process-router feature-request` bucket | Router stays the *human* Q&A entry; `intake` is the *executable* one. Router's `feature-request` row should point at `@feature-spec intake` once approved. |

## 7. If approved - implementation checklist (small)

1. Add `intake` mode to `skills/feature-spec/skill.md` (parse row + CLASSIFY/ROUTE/RECORD protocol; reuse CR0.5 for slug derivation).
2. Add the classification table to `skills/feature-spec/reference.md` as the single source.
3. Point `process-router` `feature-request` bucket → `@feature-spec intake`.
4. Add 4-sentence classifier self-test to `scripts/framework-verify.sh`.
5. CHANGELOG entry. Skill count stays 14.
