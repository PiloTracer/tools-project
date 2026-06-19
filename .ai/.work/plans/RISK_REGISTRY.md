# RISK_REGISTRY - planning registry

> **This is a template file.** In your adopter repo it is created by **`@plan-foundation`** (P0) and extended by **`@plan-master`** (architectural / ops / security risks). In this framework repo it stays as a demo skeleton.

**Updated:** YYYY-MM-DD · **Maintained by:** plan-foundation / plan-master

Status: **Open** | **Mitigated** | **Accepted** | **Closed**

| ID | Risk | Category | Likelihood | Impact | Mitigation | Status | Owner |
|----|------|----------|------------|--------|------------|--------|-------|
| R1 | Scope creep before foundation complete | process | M | M | plan-foundation gates; no broad coding until implementation-ready | Open | eng |
| R2 | Agent marks gate pass without evidence | process / agent | M | M | `.cursorrules` Completion Gate; code-verify | Mitigated | eng |
| R3 | Secrets committed to git | security | L | H | `.cursorrules` secrets scan; pre-commit | Open | eng |

## Review log

| Date | Reviewer | Action |
|------|----------|--------|
| YYYY-MM-DD | bootstrap | Initial template |
