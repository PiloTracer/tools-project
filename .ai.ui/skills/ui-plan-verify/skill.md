---
name: ui-plan-verify
description: >-
  Read-only UI plan audit: runs the framework verifiers, reports PROBE_LEDGER
  coverage and screen→milestone traceability, and surfaces gaps a script flags
  but cannot route. Use audit, probe-coverage, traceability.
---

# ui-plan-verify

Read-only audit that **surfaces** UI readiness gaps and routes them — the skill-level analogue of the scripts in `scripts/`. Mirror of Agent OS `plan-verify` **for UI scope only**. Never writes artifacts; it reports + names the next command.

**Reads:** `{UI_PLANS_ROOT}/**/PROBE_LEDGER.md`, `{UI_PLANS_ROOT}/foundation/*-04-screen-map.md`, `{HANDOFF_UI}`, `{UI_ITERATION_CARRIER}`.

## Modes

| Mode | Action |
|------|--------|
| `audit` | Run all three verifiers + summarize readiness; route each gap to a command |
| `probe-coverage` | Report per-dimension coverage from each `PROBE_LEDGER.md` (honesty-checked) |
| `traceability` | Report chain breaks: unscheduled (orphan) screens, Approved screens with no SPEC file, rogue SPEC dirs absent from the map |

## audit protocol

1. Run, capturing real exit codes (never claim PASS on failure). Paths are framework-root-relative; in an adopter repo prefix with `.ai.ui/`:

```bash
bash scripts/framework-verify.sh      # adopter: bash .ai.ui/scripts/framework-verify.sh
                                      # (also self-tests token-lint + runs bootstrap-test)
bash scripts/readiness-verify.sh
bash scripts/traceability-verify.sh   # screen↔SPEC↔milestone chain
# component token contract (adopter source; needs paths):
bash scripts/token-lint.sh --tokens REPLACE:UI_TOKENS_FILE REPLACE:UI_APP_ROOT
```

2. Read each `PROBE_LEDGER.md`: report Coverage %, any ★ dimension below `partial`, and open probes. Engine + honesty rules: [`probe-protocol.md`](../probe-protocol.md).
3. Report screen→milestone orphans (traceability) and unfilled `REPLACE:` tokens in foundation docs.
4. **Route, don't fix:** for each gap name the single next command (`@ui-design-foundation probe`, `@ui-component-build plan - S{N}`, `@ui-screen-spec create - <slug>`, …). Owner-blocked items → `{UI_PLANS_ROOT}/UNKNOWNS.md`.

## Report shape

```markdown
## @ui-plan-verify audit
**Verifiers:** framework <PASS|FAIL> · readiness <PASS|FAIL|no-ledger> · traceability <PASS|FAIL|no-map>
**Probe coverage:** foundation <NN%> (★ gaps: …) · roadmap <NN%>
**Orphan screens:** <slug…|none>
**Route:** <gap → @command> …
```

## Hard rules

- Read-only — emits no SPECs, foundation docs, or ledger edits.
- Report the verifier's real exit code; a red script is reported red.
- Routes to existing `ui-*` skills only; never invents a skill or path (fallback: [`START_HERE.md`](../../START_HERE.md) §1).

## Pairs with

- `@ui-design-foundation probe` / `@ui-component-build probe` — fill the gaps this audit surfaces
- `scripts/release.sh` — the same verifiers gate a tag
