# Mendarion - Full implementation plan

**Status:** Approved
**Version:** 1.0
**Created:** 2026-09-25
**Advanced mode:** — (none applied; the balanced default stands. The demo's speed bias is recorded as **D2** in the Decision log)
**Foundation snapshot:** plan-foundation **P0–P6 complete for revision 2** · **plan-master-ready: yes (2026-09-25)** · **implementation-ready: no** (this plan is not yet `Approved`)
**Plan owner:** owner (the operator) — review requested; the agent authored the plan and cannot approve it

> **Scope of this document.** The whole-system implementation roadmap: milestones, requirements, validation gates and agent-executable tasks. It **references** the foundation rather than restating it — ADRs live in `.work/decisions/`, SPECs in `.work/features/`, standards in `.work/standards/`, registries in `.work/plans/`. No application code is authored here.

---

## 1. Executive Summary

Mendarion is a multi-tenant clinical platform with three planes of data: a **practice tenant store** (per-tenant database + RLS), a **patient plane** (a dedicated consumer store holding the patient-owned master record) and a **PHI-free platform store** (tenant registry + the public practitioner directory index). The product serves **professionals, clinics, patients/consumers and hospitals** (A30), with the first deliverable being an **internal 2-week synthetic demo** (D-S3, U28): the revision-1 practice loop **plus** a minimal consumer path — public signup → directory browse → master file → one share grant → the clinician opens the shared file.

<mark>Developer Notes: 1) It also serves pharmacies. 2) A consumer/patient that signs up into the site to search for a practice/professional/doctor is not a tenant, for this reason he belongs to the general database.   A Doctor is a Tenant, a Clinic is a tenant, A pharmacy is a Tenant, a Hospital is a tenant. According to initial specs, a tenant has its own db for his records, data, and other tenant's data, including patients data. 2)**Analyze if hybrid tenant db approach is proper**: RLS for the bulk of small tenants where operational simplicity wins, and a dedicated database (or even a dedicated instance) for enterprise or compliance-sensitive tenants who need contractual isolation guarantees.  You can always migrate a specific tenant out of the shared pool later by routing its connection string to a dedicated database</mark>

Twelve milestones: **M1** platform skeleton (three stores, control plane, no features) → **M2** identity & assurance → **M3** consumer record + public directory → **M4** sharing & grants → **M5** the practice loop → **M6** Rx-lite → **M7** demo hardening and the acceptance run (**M1–M7 = the demo**), then the owner-fixed staged order: **M8** AI routing + Sentinel, **M9** practice self-service, **M10** live telehealth, **M11** virtual pharmacy, **M12** enterprise tier + pilot readiness.

**Top risks:** R24 (patient-facing routing is regulated triage — H/H, gated on U15), R27 (consumer identity + cross-practice sharing — H/H), R30 (Sentinel alert fatigue/missed risk — H/H), R13/MOD-04 (solo capacity; the revision adds a second database class and an object store), R19/U18 (no UI foundation exists yet — the largest delivery unknown), R33 (media in the tenant store changes the backup story). **No milestone past M1 requires a decision that is not already Decided**, but **M8, M10 and M12 are hard-gated** on U15, U29 and U13/U33 respectively, and **nothing is implemented before its SPEC is Approved**.

<mark>Developer Notes: Verify the architectural approach for this whole system allows for easy maintenance, debugging, scaling. The system must be feature-based, so that feature-vs-code establishes a clear relationship, quick location of issues, and modification of behavior.  The approach must also prevent spaghetti code, multiple-paths doing the exact same thing, and duplicate code.</mark>

---

## 2. Project Goals

| #   | Goal                                            | Success metric                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Source                    |
| --- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| G1  | Deliver the internal synthetic demo             | The demo acceptance list (doc 01 §Demo acceptance) passes end-to-end on one seeded instance; S4 journey (signup → directory → file → grant → clinician views) completes **unaided in ≤10 min**                                                                                                                                                                                                                                                                                                                            | U16/U17/U28, doc 04 §2    |
| G2  | Make the patient the real owner of their record | A revoked grant denies access **≤5 s**; no cross-plane read exists outside the grant path (test-asserted). <mark>Developer Notes: 1) at the moment a consumer accepts to become the patient of a given entity (doctor, clinic, etc.) he accepts to share his record which is cloned into the entity's store, it is possible for later to device a mechanism to allow the patient to retract that information if proper and validated. It is also possible to allow the patient to retract part of the information.</mark> | U22, ADR 011/014          |
| G3  | Make discovery trustworthy and safe             | A listing implies a verified licence + a confirmed affiliation; ordering is never payment-driven (test-asserted); no clinical field exists in the public index (build-failing test). <mark>Developer Notes: 1) For later integration, automatic status checks vs the licensing authority in the given jurisdiction.</mark>                                                                                                                                                                                                | U27, ADR 013              |
| G4  | Keep AI advisory and auditable                  | Every AI output carries provenance; nothing is auto-applied; each job type is enabled only after its evaluation bar passes                                                                                                                                                                                                                                                                                                                                                                                                | ADR 007/016/017, S3/S5/S6 |
| G5  | Reach the practice-side pilot targets           | S1 engagement, S2 clinical movement, S3 AI usefulness (accept rate ≥30%) measurable in production                                                                                                                                                                                                                                                                                                                                                                                                                         | doc 01 §Success criteria  |
| G6  | Be operable by one person                       | Every routine operation is a `bin/start.sh` verb; backup/restore covers all stores and objects; no undocumented manual step                                                                                                                                                                                                                                                                                                                                                                                               | A12/A23, ADR 008          |

<mark>Developer Notes: 1) A consumer/patient that signs up directly is never a tenant (this was mentioned above as well), but 2) a Tenant can have a consumer/patient copied into its own tenant records, 3) a Tenant can have multiple professionals copied into its tenancy, for example a Doctor may have several collaborators under his practice, and each of those colaborators can be independent tenants themeselves, similarly to a Clinic, or a Hospital.</mark>

---

## 3. Functional Requirements

Each FR is testable and traceable to ≥1 task in §19 and to a SPEC rule where one exists.

| ID   | Requirement                                                                                                                                                                                                                                                                                                                                        | SPEC / ADR                                       |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| FR1  | A person can create an account, verify email + phone, reach assurance **L1**, sign in, recover, and close the account                                                                                                                                                                                                                              | `consumer-onboarding` R1–R6, R12–R16 · ADR 012   |
| FR2  | A professional/clinic appears in the public directory only after **L2** (licence verified + affiliation confirmed by the tenant admin), and is delisted on lapse                                                                                                                                                                                   | `directory-discovery` R3–R5 · ADR 012/013        |
| FR3  | Anyone can search and view the directory **without an account or session**, with no clinical field in the index                                                                                                                                                                                                                                    | `directory-discovery` R1/R2/R7 · ADR 013         |
| FR4  | A patient owns a master file (demographics, conditions, allergies, medications, occupation/job-safety class) and can edit it                                                                                                                                                                                                                       | `consumer-onboarding` R7–R10                     |
| FR5  | A patient can grant a clinician scoped, time-boxed read access to named sections, see who exercised it, and revoke it with immediate effect.  <mark>Developer Notes: A tenant seeing the patient will continue to keep the part of the data he has generated, like prescriptions, notes, follow-up, transcripts, meetings, references, etc.</mark> | `record-sharing` R1–R13 · ADR 014                |
| FR6  | A clinician can open a shared file and receive **only** the grant-covered sections.  <mark>Developer Notes: the clinician's added data will remain property of the clinician, with basic reference data from the patient.</mark>                                                                                                                   | `record-sharing` R4/R12                          |
| FR7  | A patient can submit a check-in (adherence, symptom/pain, mood, free text) from an authenticated account                                                                                                                                                                                                                                           | `check-in-feedback` R2/R3 + amendment 01 R14–R17 |
| FR8  | Free text is stored verbatim and a deterministic redacted twin is produced before any egress; failure blocks the AI job                                                                                                                                                                                                                            | `check-in-feedback` R4/R5                        |
| FR9  | Threshold rules raise attention flags a clinician sees, and the cockpit shows a 30-day trend                                                                                                                                                                                                                                                       | `check-in-feedback` R7 · doc 04 §3 BC4           |
| FR10 | AI **feedback triage** produces advisory suggestions with provenance and accept/reject/correct capture                                                                                                                                                                                                                                             | `assist-ai` R2–R10                               |
| FR11 | AI **medication research** answers a clinician question with citations, advisory only                                                                                                                                                                                                                                                              | `assist-ai` R8                                   |
| FR12 | **Rx-lite**: a medication list with start/stop/dose history per patient (the demo's scope; not the prescribing write path)                                                                                                                                                                                                                         | *new SPEC required — M6-T1*                      |
| FR13 | AI **routing**: a patient's plain-language question returns a ranked shortlist with a rationale, never a diagnosis, with tiered staff-confirmation gating and a red-flag bypass                                                                                                                                                                    | `assist-ai` amendment 01 R18–R22 · ADR 016       |
| FR14 | **Sentinel**: deterministic medication-safety alerts from a licensed data source, clinician-first, cited, override-with-reason, never a silent block.  <mark>Developer Notes: would these services fit here: RxLabelGuard, DrugsAPI, RxCheck, openFDA?</mark>                                                                                      | `assist-ai` amendment 01 R23 · ADR 017           |
| FR15 | **Prescribing write path**, opt-in per tenant; network transmission stays V3                                                                                                                                                                                                                                                                       | ADR 010 (**staged, M8**)                         |
| FR16 | **Live telehealth**: clinician↔patient video from the chart, browser join, waiting room/device check, audio-only + dial-in fallback, opt-in recording to the owning store                                                                                                                                                                          | ADR 009/015 (**staged, M10**)                    |
| FR17 | A licensed pharmacy partner can receive a prescription; **Mendarion never dispenses**                                                                                                                                                                                                                                                              | ADR 010, I5 (**staged, M11**)                    |
| FR18 | A practice can invite members, assign roles and manage its subscription                                                                                                                                                                                                                                                                            | **staged, M9**                                   |
| FR19 | An enterprise/hospital tenant gets dedicated isolation (and optionally dedicated media), SSO and extended audit                                                                                                                                                                                                                                    | ADR 011/009 (**staged, M12**)                    |
| FR20 | The platform operator can provision a tenant with a **tier** and migrate it between tiers                                                                                                                                                                                                                                                          | ADR 011 · `bin/start.sh tenants`                 |
| FR21 | Patients and medications can be imported from CSV (idempotent, dry-run, per-row report)                                                                                                                                                                                                                                                            | doc 02 I2                                        |
| FR22 | Every clinical write and PHI access (including grant resolutions and media join/leave) emits an append-only audit event                                                                                                                                                                                                                            | `check-in-feedback` R6 · `record-sharing` R6/R8  |
| FR23 | All user-facing strings come from locale keys; EN ships and ES keys exist                                                                                                                                                                                                                                                                          | R17 / ADR 006                                    |
| FR24 | A patient sees the AI-generated safety information **only after** a clinician has seen it (Sentinel patient copy staged on U15)                                                                                                                                                                                                                    | ADR 017 §3                                       |

<mark>Developer Notes: A critical goal of the system is to make the clinician's work easier, simplification of his tasks is of great importance for the success of this application.</mark>

---

## 4. Non-Functional Requirements

Operative targets are doc 04 §5; signal names are the observability spec's contract.

| ID    | Target                                                                                                                                                                                     | Source                                   |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| NFR1  | Clinician cockpit read p95 < 1.5 s (p99 < 3 s)                                                                                                                                             | doc 04 §5                                |
| NFR2  | Patient check-in submit p95 < 1 s on a 4G phone; patient route JS ≤ 150 KB                                                                                                                 | doc 04 §5, `check-in-feedback` R12       |
| NFR3  | AI suggestion visible p95 < 30 s; provider failure degrades silently to "no suggestion"                                                                                                    | doc 04 §5/§7                             |
| NFR4  | Availability 99.5% (practice tier) / **99.9%** (enterprise tier) monthly                                                                                                                   | doc 04 §5                                |
| NFR5  | Nightly encrypted backups, RPO ≤ 24 h, RTO ≤ 4 h in the demo tier (1 h/15 min from the pilot); **all three stores and objects are covered**                                                | doc 04 §5, ADR 015 §7                    |
| NFR6  | Tenant isolation enforced in the data-access layer with RLS as defence-in-depth; **plane isolation** enforced in the same layer; a cross-tenant **and** cross-plane read returns zero rows | ADR 002/011/014                          |
| NFR7  | Raw PHI never crosses a boundary: redaction is fail-closed before egress; every cross-store read is grant-covered                                                                          | ADR 005/014                              |
| NFR8  | No PII/PHI in logs, traces, metric labels, error bodies or URLs (ids only)                                                                                                                 | data-classification §2, observability §7 |
| NFR9  | WCAG 2.2 AA on the patient/consumer flow **and** the public directory path; AA-targeted cockpit                                                                                            | doc 04 §5, directory R13                 |
| NFR10 | i18n structural: EN shipped, ES keys present and parity-asserted.<mark>  Developer Notes: Both EN + ES must be supported from the beginning.</mark>                                        | `check-in-feedback` R10                  |
| NFR11 | Public directory search p95 < 300 ms                                                                                                                                                       | doc 04 §5, directory R10                 |
| NFR12 | **Grant revocation effective ≤ 5 s**, measured (`grant_revocation_latency_seconds`)                                                                                                        | ADR 014 R5                               |
| NFR13 | Consumer signup p95 < 2 s                                                                                                                                                                  | doc 04 §5                                |
| NFR14 | Live media: 720p target, audio survives < ~1 Mbps, one-way latency < 300 ms; automatic audio-only + dial-in fallback                                                                       | doc 04 §5                                |
| NFR15 | AI spend ≤ 5% of per-seat revenue with a per-tenant cap; every model call is metered                                                                                                       | doc 04 §5, `assist-ai` R10               |
| NFR16 | Audit completeness 100% of PHI accesses recorded; `audit_write_failures_total` stays 0                                                                                                     | observability §6                         |
| NFR17 | Retention: clinical records and recordings **7 years** default, policy-driven lifecycle for objects                                                                                        | U31, ADR 015 §5                          |
| NFR18 | The public directory index is **PHI-free by construction**, asserted by a build-failing classification test                                                                                | directory R2/I1                          |

---

## 5. Constraints

- **Team = 1 developer** (A12); **demo deadline ~2 weeks** from implementation start; budget is not a tracked constraint (A23, U9).
- **Deliverable = internal demo on synthetic data** (A20, U16) — no production PHI, no vendor BAAs needed for the demo, mock identity verification, no live AI vendor required.
- **Stack is pinned** (`DOCS_TECH_STACK.md`): Python 3.12 + FastAPI · PostgreSQL 17 per tenant with RLS · a separate patient-plane PostgreSQL store · Redis 7.4 (cache + Streams) · object storage (service Deferred → U33) · one Next.js + TypeScript app · Fly.io-class hosting, region Deferred (U13).
- **Process constraints:** every feature needs an **Approved** SPEC; `bin/start.sh` is the only supported dev path (ADR 008); protected files need same-message owner approval; agents never commit without an explicit instruction.
- **Regulatory:** patient-facing routing is triage (R24); patient-facing Sentinel copy is staged; neither ships without U15 sign-off. Jurisdiction/residency (U13) gates the pilot, not the demo.

---

## 6. Assumptions

Inline summary only — the canonical, labelled list is `.work/plans/ASSUMPTIONS.md` (A1–A38).

- **Confirmed:** single developer; 2-week demo; synthetic data only; global market EN-first; AI advisory with redaction before egress (A12, A17, A20, A2/A11, A14/A15); two tenancy tiers + a **dedicated consumer store** for the patient plane (A35, owner 2026-09-25); tiered routing gating (A36); the P2 ADR set ratified as a batch (A37).
- **Inference (labelled, revisitable):** the prescribing surface is opt-in per tenant (A34); object storage is *Deferred with a fixed pattern* rather than undecided (A38).
- **Unverified:** R22 — no independent review of the compliance-critical ADRs yet.

## 7. Risks

Top risks (canonical list: `.work/plans/RISK_REGISTRY.md`, R1–R33). Those that shape this plan:

| Risk                                                                    | Why it shapes the roadmap                  | Mitigation in the plan                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R19/U18** — no UI foundation, and the revision adds two more surfaces | Could sink the 2-week demo on its own      | M1-T11 scaffolds route groups; M2–M6 build the demo's screens with a minimal in-house component set and record the divergence; `@ui-bootstrap` is the owner action.  <mark>Developer Notes: should I have the ui-director to create the ui foundational plan?</mark>      |
| **R24** — routing is regulated triage (H/H)                             | M8 cannot enable routing on code alone     | M8-T7 (evaluation harness) + M8-T8 (U15 wording gate) are prerequisites of enablement, not follow-upsDeveloper Notes: should I have the ui-director to create the ui foundational plan?Developer Notes: should I have the ui-director to create the ui foundational plan? |
| **R13/MOD-04** — solo capacity; a second DB class + object store        | The revision's real ops cost               | M1-T5/T6 build store provisioning + backup coverage *before* features; M12 formalises ops                                                                                                                                                                                 |
| **R27** — consumer identity + cross-practice sharing (H/H)              | The demo's consumer path is the risky half | M2 and M4 implement assurance + grants with their tests first (deny-by-default, ≤5 s revocation, access log)                                                                                                                                                              |
| **R30** — Sentinel alert fatigue / missed risk (H/H)                    | Safety-critical, negative eval both ways   | M8-T9–T11: deterministic rules, cited basis, logged overrides, override-rate review, S6 gate                                                                                                                                                                              |
| **R33** — media in the tenant store                                     | Changes backup/RPO/RTO                     | M10-T6/T7 land the storage + lifecycle + backup coverage with the recording feature, not after it                                                                                                                                                                         |
| **R14/R15** — AI quality and cost                                       | Recurring; gates each job type             | Evaluation harness per job type (M5-T9, M8-T7) + metered spend (M5-T10)                                                                                                                                                                                                   |
| **R20** — no CI                                                         | A skipped gate is invisible                | M12-T2 adds the pipeline; until then every task carries its validation command                                                                                                                                                                                            |
| **R22** — unreviewed compliance ADRs                                    | The plan hardens them as immutables        | Recorded as a plan-level open item; owner action before M1 starts                                                                                                                                                                                                         |

## 8. Unknowns / Open Questions

Inline summary — canonical list `.work/plans/UNKNOWNS.md`. **Every revision-2 foundation unknown is closed** (U21–U28, U31, U34). Open, with owners, and what they gate in this plan:

| Unknown                                                                        | Gates                                                                                                                                                                                                            | Owner                       |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **U15** — patient-facing AI wording + evaluation pass bars (routing, Sentinel) | **M8 enablement** (not authorship); `assist-ai` + amendment 01 approval                                                                                                                                          | internal CTO collaborator   |
| **U29** — telehealth vendor + BAA                                              | **M10** (all of it)                                                                                                                                                                                              | owner (contract) + eng      |
| **U30** — licensed clinical drug-data source                                   | **M8** Sentinel rules' usefulness (the deterministic engine can be built against a stub).<mark>Developer Notes (duplicate note): would these services fit here: RxLabelGuard, DrugsAPI, RxCheck, openFDA?</mark> | owner (licence) + eng       |
| **U33** — object-storage service + residency + cost                            | **M10** recording; the demo only needs the interface                                                                                                                                                             | eng (+ owner for residency) |
| **U13** — jurisdiction + residency                                             | **M12**/pilot; the enterprise tier; the media vendor's and stores' placement                                                                                                                                     | owner                       |
| **U14** — AI vendor agreement + redaction evidence                             | Real-patient AI use (not the demo, which is synthetic)                                                                                                                                                           | owner                       |
| **U32** — Compass data dependencies                                            | M8's richer filters / V2 reviews                                                                                                                                                                                 | owner                       |
| **U6 / U12 / U2 / U18 / U19**                                                  | Milestone priority after the demo · billing design · CI · UI foundation · the Redis keep/remove review                                                                                                           | owner/eng                   |

## 9. Architecture Overview

**Style:** a **modular monolith** — one API deployable (ADR 001) containing 13 bounded contexts as packages, one Next.js app (ADR 006), Redis for transport/cache (ADR 003), and **three PostgreSQL planes** (ADR 011). Full detail: `.work/plans/foundation/20260924-04-foundation-architecture.md` §3/§4; packages: `.work/standards/20260924-DIRECTORY_MAP.md` §2; boundary rules: the same document §3.

```text
Next.js app (Dockerfile.dev|prd)
  (public)/directory      (consumer)/signup,file,grants,checkin      (clinician)/panel,rx,cockpit
        |                        |                                        |
        +------------------------+------ /v1 HTTPS --------+--------------+
                                                                 |
                              FastAPI (one deployable, ADR 001)
   identity | panel | consumer_record | directory | sharing | checkin | cockpit
   assist   | live  | safety          | prescribing | ingestion | platform
        |                         |                            |
   tenant store (per-tenant DB)  patient plane (consumer DB)  platform store (PHI-free)
        +------------- shared/{db,tenancy,planes,queue,cache,audit,storage,i18n,errors,logging}
                                                                 |
                                          Redis 7.4 (Streams + cache + invalidation)
                                          Object storage (ADR 015 pattern; service → U33)
```

**The three invariants** (doc 04 §1, all test-asserted): tenant scoping at the data-access layer; **no raw PHI crossing a plane boundary**; **every cross-store read passes the grant service**.

## 10. UX/UI Strategy

<mark>Developer Notes: I will have the UI Foundation Plan ready before starting to execute the Implementation of the system.  Code implementation must orchestrate both functionality code and UI plan. Provide directions on how to fully remove the Blocking gap reported below.</mark>

- **Inputs:** `.work/plans/20260924-personas-v1.md` rev 2 (P1–P10, journeys J1–J7 with budgets) is the contract handed to the UI Design OS; screens live in `.work.ui/` and are **not** authored by Agent OS.
- **Blocking gap:** `@ui-bootstrap` → `@ui-design-system` → `@ui-screen-spec` (U18/R19). **Fallback recorded:** if the UI foundation cannot land in time for the demo, build the demo's screens with a minimal in-house component set (tokens inline, no design system) and record the divergence in `RISK_REGISTRY` — the demo is judged on the journey working, not on visual polish.
- **Three surfaces, three audiences:** public (no session, indexable, zero PHI), consumer (mobile-first, WCAG 2.2 AA, 150 KB JS budget), clinician (desktop, keyboard-first, no page reloads).
- **Shared grammar** across pillars (concept §4); every list/chart needs loading, empty and error states (the P3 review's `partial` rows), now including assurance-pending, delisted professional, grant-expired and residency-blocked.
- **Always-legible affordances:** the AI advisory label + rationale on every AI element; the grant scope and revocation in one action; the recording-consent state to both participants; the Sentinel override with a reason.

## 11. Data Strategy

- **PostgreSQL 17, three plane roles** (ADR 002 + **011**): **tenant store** — one database per practice tenant, RLS inside; **patient plane** — a dedicated consumer store with per-person isolation (no `tenant_id`); **platform store** — PHI-free, holds the tenant registry and the public directory index.
- **Entities:** doc 04 §6 (per plane); **classification:** `20260924-data-classification.md` §3 tags every revision-2 table, and the public index has a **build-failing** rule against an unclassified field.
- **Migrations:** numbered, idempotent SQL under `apps/api/migrations/`, applied **per store** by `mendarion.shared.migrate` at boot, in order; runners are verified by running twice on a dev database; destructive statements need same-message owner approval.
- **Retention/erasure:** 7 years clinical (and recordings) by default via **storage lifecycle rules** for objects (NFR17); erasure spans all three stores and their objects (U13 finalises the windows).
- **No copies across planes** (U22/ADR 014) — sharing is grants resolved at read time. <mark>Developer Notes: (Maybe non-related to the "no copies across planes") - This doesn't exclude for example, a tenant can copy minimal data from a patient's record, A Tenant can copy minimal data from another tenant/clinician.</mark>
- **Search:** Postgres full-text in the tenant store for feedback; the directory index is a projected, allowlisted table (ADR 013 §8).

## 12. Security Strategy

<mark>Developer Notes: Before MVP is deployed into production, a full scan from SOC OS Framework is required, this includes both strix, OWASP scans, and other security tests.</mark>

Threat model: `20260924-threat-model.md` (revised for revision 2 — boundaries **T1–T10**, assets A1–A8c, STRIDE extended). Controls in force from M1:

- **AuthN/AuthZ:** staff email+password+MFA; consumer accounts with contact verification and **assurance levels L0/L1/L2** (ADR 012); tenant context from **membership**, plane context from the request's plane — never from a parameter (api-style-guide §2).
- **Isolation:** data-access-layer scoping + RLS per tenant DB + per-person scoping in the patient plane; the **grant service is the only cross-plane path**; a `directory` projection is one-way, field-allowlisted and classification-tested.
- **PHI egress:** one adapter (BC5), fail-closed redaction, contract at U14; transcripts keep the same rule.
- **Secrets:** environment only; `.env.dev`/`.env.prd` git-ignored; stub verification channels **boot-guarded out of `prd`** (consumer-onboarding I5). <mark>Developer Notes:  Encrypted secrets in database can override some values in the .env.dev/.env.prd file. Which values can be overwritten needs to be defined properly, mainly those values that are suitable for modification, and restarting the stack or a service must be avoided.</mark>

- **Data classification** enforced by tag + tests; no PHI in telemetry (NFR8).
- **Objects:** short-lived signed URLs issued only after the owning service's own authorisation check; issuance audited.
- **Residual accepted risks:** the affiliation **four-eyes** gap (consumer-onboarding §13.2, M2-T12), the un-reviewed ADRs (R22), and the demo's mock verification.

## 13. Infrastructure Strategy

- **Environments:** `dev` (hot reload, published ports) and `prd` (production images) via one control plane — `bin/start.sh` (ADR 008). Compose project isolation through `STACK_SUFFIX`.   <mark>Developer Notes: There must exist 3 .env* files: .env.prd, .env.dev, .env.example, all with 1-to-1 line-correspondence for all the environment variables. You must generate the 3 files and keep them consistent.</mark>
- **Services (demo):** `api`, `web`, **`db` (tenant store)**, **`consumer-db` (patient plane)**, **`platform-db`**, `redis`. *(M1-T5/T6 add the two new database services and the backup/restore coverage.)*
- **Object storage:** not containerised in the demo; the interface (`shared/storage.py`) exists from M1 and the local adapter is a filesystem/volume stub until U33 selects the service (M10). <mark>Developer Notes: I may also provide a "Seaweed FS" instance.</mark>
- **Hosting:** Fly.io-class, single region (ADR 004); region Deferred (U13). No Kubernetes, no orchestrator.  <mark>Developer Notes: A honest assessment must be made in order to determine the suitability of Fly.io-class to host this application.</mark>
- **Control-plane growth:** `tenants`/`tenant-create`/`backup`/`restore`/`migrate` must cover **all three stores** by the end of M1 (a hard task, not an aspiration).

## 14. Deployment Strategy

- **CI:** none today (U2/R20) — every task carries its validation command; **M12-T2** adds a pipeline (GitHub Actions on the private repo: lint, type, unit+integration, migration idempotency, OpenAPI diff, MOD-06 record).
- **CD:** manual by design for the demo (`./bin/start.sh --env prd smoke` → `deploy`, which stops at the deploy-target gate until U13). Rolling replacement of a single service; no blue/green (one deployable, small blast radius).
- **Migrations:** run before the app serves traffic, per store; additive and idempotent; a breaking change requires a two-step release (expand → migrate → contract).
- **Feature flags are the deployment unit for risk:** `consumer.signup.enabled`, `directory.enabled`, `sharing.enabled`, `checkin.enabled`, `assist.*`, `directory.sponsored.enabled`, `sharing.residency.strict`.**Migrations:** run before the app serves traffic, per store; additive and idempotent; a breaking change requires a two-step release (expand → migrate → contract).

## 15. Scalability Strategy

- **Pilot envelope:** 1 clinic, ≤10 clinicians, ≤5k patients, ≤50k check-ins/year, K–M rows per tenant (doc 04 §5). No horizontal scaling claim is made for the demo.
- **Named seams:** (a) per-tenant database connections — revisit with the SMB pool ADR before dozens of tenants (ADR 002); (b) **the patient plane's per-person store dimension** — a capacity note is required before the pilot (the P3 review's finding); (c) the AI worker is decoupled via Redis Streams so provider latency never blocks a request.
- **Caching:** tenant-scoped aggregates + medication lookups behind `shared/cache.py`; grant-resolution caching with a **sub-5 s TTL** + invalidation broadcast (ADR 014). U19 reviews whether the cache earns its place.
- **Queues:** Redis Streams with consumer groups, leases and dead-lettering; a job table remains the system of record.
- **The public directory** is the one surface that may be cached aggressively (public content, no session, CDN-friendly).

<mark>Developer Notes: **Horizontal-Scaling Readiness Requirements (pilot phase)** -> The system must be architecturally prepared for horizontal scale-out (sharding, replication, multi-instance) without requiring a rewrite. Enforce the following from day one: 1) **Shard key in schema:** Every tenant-scoped table carries `tenant_id NOT NULL` as the leading column in all composite indexes. No tenant-scoped query may omit a `tenant_id` predicate. A sharding strategy that allows automatic creation of new shards is better, and probably best approach is inhouse sharding strategy as opposed to 3rd party plugins. 2) **Stateless app tier:** Sessions → external store (Redis/JWT). File uploads → object storage. Caches → external. Background jobs → durable queue. Killing any instance mid-request must lose nothing. 3) **ID strategy:** Use UUIDv7 or composite keys `(tenant_id, local_seq)`. No global `SERIAL`/`AUTO_INCREMENT` as the sole primary key on tenant-scoped tables. 4) **No cross-tenant FKs:** Foreign keys must not reference rows in a different tenant. Cross-tenant lookups, if needed, must be explicit and flagged. 5) **Externalized config & infra:** Connection pooling (PgBouncer or equivalent) in place. All config via env vars. Logging/metrics shipped to a centralized collector. 6) **Per-tenant observability:** Track rows written, p95 query latency, and connection count per tenant from the first deployment. This is the input for future shard-placement decisions. **Out of scope for pilot:** multi-node DB deployment, shard router, read replicas, load balancer. These are deferred to the scale-out phase and are expected to be straightforward ops changes given the above.</mark>

## 16. Observability Strategy

Contract: `.work/standards/20260924-observability-spec.md` (metric/span/log names are binding; revised for revision 2). In force from M1: structured JSON logs with ids only, `http_request_duration_seconds`, `migration_run_duration_seconds`, `audit_write_failures_total`. Added with their features:

- **Loop:** `checkin_submit_seconds`, `checkin_redaction_failures_total`, `attention_flags_raised_total`, `checkin_to_suggestion_seconds`.
- **AI:** `ai_job_duration_seconds`, `ai_job_failures_total`, `ai_suggestions_created_total`, `ai_suggestion_accept_rate`, `ai_tokens_total`/`ai_cost_minor_units`, `ai_dead_letter_total`.
- **Sharing:** `grant_resolutions_total`, **`grant_revocation_latency_seconds`** (the NFR12 SLI), `grant_denied_total`, `object_url_issued_total`.
- **Directory/identity:** `directory_search_seconds`, `directory_projection_lag_seconds`, `directory_delistings_total`, `consumer_signup_seconds`, `assurance_transitions_total`.
- **Staged:** `route_confirmation_required_total`, `sentinel_alerts_total`/`sentinel_overrides_total`, `sentinel_rule_source_age_seconds`, `live_*`, `compass_match_*`.
- **Alerts** (P6 wiring): audit writes failing (page), redaction failing (page), **grant revocation lagging > 5 s (page)**, residency-blocked resolutions, directory delisting spike, AI provider down, budget exhausted, loop degradation.

## 17. Testing Strategy

- **Levels:** unit (`pytest`, vitest) · integration against **real containers** for all three stores (testcontainers) · API contract (OpenAPI diff) · e2e/a11y (Playwright: patient check-in, consumer sign-up→share, clinician triage, directory browse) · migration idempotency (run twice) · load smoke (p95 assertions for NFR1–NFR3, NFR11–NFR13).
- **Rule-driven:** every SPEC R-rule has a named test in its §11; a PR lists the R-rules it implements.
- **Security tests that must exist before the demo:** cross-tenant read returns zero rows; **cross-plane read without a grant is denied** (and no foreign-plane content is persisted); redaction failure blocks egress; **no PII in logs/traces** (capture scan); **the directory index has no clinical column**; grant revocation ≤5 s; the stub verification channel refuses `prd` boot.
- **Coverage target:** no percentage target; the gate is **rule coverage** (every R-rule mapped to a test) plus the security list above.
- **CI gates** arrive at M12; until then the validation commands in §21 are run per task and reported.

## 18. Operational Strategy

- **Runbooks:** `bin/start.sh` verbs are the runbook surface (`up`, `status`, `logs`, `health`, `migrate`, `tenants`, `tenant-create`, `backup`, `verify-backup`, `restore`, `prune-backups`, `smoke`) — extended in M1 to the second database class.  <mark>Developer Notes: other verbs are "rebuild", "restart", "cleanup" (no volume removal), "reset" (full reset of stack).</mark>
- **Incident classes:** data-isolation (page), PHI-egress/redaction (page), **grant-revocation lag (page)**, audit-write failure (page), provider/budget (ticket), directory-projection drift (ticket). Containment paths are in the threat model §6.
- **On-call:** the owner (1 developer). Alerts must be actionable or deleted (observability §1.4).
- **Backups:** nightly per store + objects, with a **verified restore** drill recorded before the demo is declared done (M7-T6).
- **Synthetic-data rule:** no production PHI anywhere in dev, CI or prompts (A7/A20).

<mark>Developer Notes: a critical area of the system is "Notifications". The system must support notification through "email", "whatsapp", "signal", "telegram", "sms" (deferred integration).</mark>

## 19. Incremental Execution Roadmap

### Milestone overview

| #   | Milestone                                        | Scope                                                 | Gate                                           |
| --- | ------------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------- |
| M1  | Platform skeleton, three stores, control plane   | infra only, no product features                       | walking skeleton deployed locally, tests green |
| M2  | Identity & assurance (BC1)                       | accounts, L1/L2, sessions, recovery                   | signup journey + assurance tests               |
| M3  | Consumer record + public directory (BC8/BC9)     | master file, index, projection, browse                | directory PHI-free test + browse               |
| M4  | Sharing & grants (BC10)                          | grants, resolver, revocation, access log              | ≤5 s revocation test                           |
| M5  | The practice loop (BC2/BC3/BC4/BC5)              | panel, check-in, redaction, flags, cockpit, AI triage | loop e2e + fail-closed tests                   |
| M6  | Rx-lite                                          | medication list + history (+ its SPEC)                | list/history e2e                               |
| M7  | Demo hardening, seed & acceptance run            | seeded tenant, demo script, S4 timing, restore drill  | **the demo acceptance list passes**            |
| M8  | AI routing + Sentinel (+ prescribing write path) | staged 1st                                            | S5/S6 harness + U15 gate                       |
| M9  | Practice self-service                            | staged 2nd                                            | invitations/roles/subscription                 |
| M10 | Live telehealth + recording                      | staged 3rd                                            | media NFRs + U29 gate                          |
| M11 | Virtual pharmacy (partner)                       | staged 4th                                            | partner integration (never dispense)           |
| M12 | Enterprise tier + pilot readiness                | dedicated isolation, SSO, CI, compliance              | pilot gate (U13/U14/U15)                       |

---

### M1 — Platform skeleton, three stores and the control plane

**Objective:** a running, testable skeleton with all three data planes, one seeded tenant, health/readiness, logging/audit interfaces and an extended control plane — **no product features**.
**Scope — in:** repo layout per DIRECTORY_MAP §2; FastAPI assembly + settings; three stores provisioned and migrated; the `shared/` interfaces; the Next.js shell with `(public)/(consumer)/(clinician)` route groups and locale files; testcontainers harness; OpenAPI generation; `bin/start.sh` extended to the second database class.
**Scope — out:** every product feature; the object-storage **service** choice (U33 — interface + local stub only); CI (U2 → M12).
**Dependencies:** plan `Approved`; the two protected-file changes this needs (`docker-compose.*`, `bin/start.sh`) require owner approval in the same message.
**Deliverables:** `apps/api/src/mendarion/**` skeleton, `apps/api/migrations/001_*.sql`…, `apps/web/app/**`, the extended `bin/start.sh`, `apps/api/tests/` harness.
**Complexity:** L · **Operational impact:** the stack gains two database services and backup coverage.
**Testing requirements:** integration tests against three containers; migration idempotency (×2); a cross-tenant and a cross-plane read must return zero rows; `readyz` fails when a store is down.

#### Tasks - M1: platform skeleton

| ID     | Description                                                                                                                                                 | Files                                                                                               | FR/NFR      | Complexity | Status  |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------- | ---------- | ------- |
| M1-T1  | Provision repo layout exactly as `DIRECTORY_MAP` §2 (contexts named, staged packages empty)                                                                 | `apps/api/src/mendarion/**`, `apps/web/app/**`                                                      | —           | S          | pending |
| M1-T2  | FastAPI app assembly: config from env, problem+json errors, correlation ids, routers by context                                                             | `apps/api/src/mendarion/main.py`, `config.py`, `shared/errors.py`                                   | NFR8        | M          | pending |
| M1-T3  | Structured PHI-safe logging + middleware (ids only) with a log-capture test                                                                                 | `apps/api/src/mendarion/shared/logging.py`                                                          | NFR8        | S          | pending |
| M1-T4  | Append-only audit writer + `audit_write_failures_total` metric; migration for `audit_events`                                                                | `shared/audit.py`, `migrations/`                                                                    | FR22, NFR16 | M          | pending |
| M1-T5  | **Three-plane data access:** `shared/db.py` (per-store engines), `shared/tenancy.py` (tenant → DB), `shared/planes.py` (plane resolver + cross-plane guard) | `shared/db.py`, `tenancy.py`, `planes.py`                                                           | NFR6        | L          | pending |
| M1-T6  | Extend the control plane: `consumer-db` + `platform-db` services, `migrate` across stores, `backup`/`verify-backup`/`restore` coverage, health checks       | `docker-compose.dev.yml`, `docker-compose.prd.yml`, `bin/start.sh` **(protected — owner approval)** | NFR5        | L          | pending |
| M1-T7  | Migration runner applied per store, alphanumeric, idempotent; run-twice test                                                                                | `apps/api/src/mendarion/shared/migrate.py`, `migrations/`                                           | NFR6        | M          | pending |
| M1-T8  | `shared/queue.py` (Streams producer/consumer) + `shared/cache.py` (tenant-scoped, TTL policy) interfaces                                                    | `shared/queue.py`, `cache.py`                                                                       | NFR3        | M          | pending |
| M1-T9  | `shared/storage.py` interface (signed URLs, lifecycle hooks) + a local filesystem adapter (service → U33)                                                   | `shared/storage.py`                                                                                 | NFR17       | M          | pending |
| M1-T10 | `shared/i18n.py` + `apps/web/messages/{en,es}.json` with a parity test                                                                                      | `shared/i18n.py`, `apps/web/messages/`                                                              | FR23, NFR10 | S          | pending |
| M1-T11 | Next.js shell: `(public)/(consumer)/(clinician)` route groups, locale wiring, a11y baseline, JS budget check                                                | `apps/web/app/**`, `next.config.ts`                                                                 | NFR2, NFR9  | M          | pending |
| M1-T12 | Test harness: containers for all three stores + the security test skeletons (cross-tenant, cross-plane, no-PII-in-logs)                                     | `apps/api/tests/{unit,integration}`                                                                 | NFR6/8      | M          | pending |
| M1-T13 | Tenant registry + `tier` attribute + `tenant-create` for practice and enterprise tiers; seed one demo tenant                                                | `platform/`, `bin/start.sh` verb                                                                    | FR20        | M          | pending |

**Acceptance criteria:** `./bin/start.sh test|lint|type` green; `./bin/start.sh --env dev up` brings up api/web/three stores/redis; `readyz` reflects store health; a cross-tenant and a cross-plane query return zero rows (asserted); migration runner is idempotent; `docker compose config` validates both environments.
**Validation steps:** `./bin/start.sh test` · `lint` · `type` · `--env dev up` + `health` · `migrate` twice · `backup` + `verify-backup`.
**Rollback:** additive only — disable the new services and revert the compose/script change (protected-file approval needed in the same message). No data migration exists yet.
**Testing requirements:** unit + integration (three containers) + migration idempotency + the two isolation assertions.

---

### M2 — Identity and assurance (BC1)

**Objective:** real accounts with assurance levels, so both populations the product serves can be modelled.
**Scope — in:** signup, contact verification (stub channels, boot-guarded out of `prd`), sessions, memberships, assurance **L0/L1/L2**, `professional_affiliation` (tenant-admin confirmation), password reset, closure request, locale strings.
**Scope — out:** real licence-registry calls (U13), minors/guardianship, staff MFA enrolment UI beyond the demo's needs, SSO (M12).
**Dependencies:** M1. **SPEC:** `consumer-onboarding` **must be Approved** first.
**Deliverables:** `apps/api/src/mendarion/identity/**`, `apps/web/app/(consumer)/signup|verify/**`, migrations, tests.
**Complexity:** L · **Operational impact:** new auth surface; rate limits; session store.

#### Tasks - M2: identity and assurance

| ID     | Description                                                                                                                  | Files                         | FR/NFR       | Complexity | Status  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------ | ---------- | ------- |
| M2-T1  | `consumer_account` + unique normalised email + password policy; **uniform** responses (no enumeration)                       | `identity/`, `migrations/`    | FR1, NFR13   | M          | pending |
| M2-T2  | Contact verification: hashed single-use tokens, ≤15 min TTL, per-contact/IP rate limits, both-channel rule for L1            | `identity/verification.py`    | FR1          | M          | pending |
| M2-T3  | Stub verification channel + **`prd` boot guard** (fail closed outside the demo)                                              | `identity/channels/`          | FR1          | S          | pending |
| M2-T4  | Session issue/refresh/revoke (HttpOnly/Secure/SameSite, short patient TTL), revoke-all on password/contact change            | `identity/sessions.py`        | FR1, NFR7    | M          | pending |
| M2-T5  | `identity_assurance` storage + state machine (monotonic, revocable, never inferred)                                          | `identity/assurance.py`       | FR1          | M          | pending |
| M2-T6  | `membership` (patient-of-tenant, staff) as the only tenant-context source for a person                                       | `identity/membership.py`      | FR1, NFR6    | M          | pending |
| M2-T7  | `professional_affiliation` + tenant-admin confirmation endpoint (staff session, tenant-scoped)                               | `identity/affiliation.py`     | FR2          | M          | pending |
| M2-T8  | Licence-check **adapter** (stub records the intended registry call + evidence shape)                                         | `identity/licence_adapter.py` | FR2          | M          | pending |
| M2-T9  | Password reset (single-use, revokes all sessions) + closure request (blocks new sessions/grants)                             | `identity/recovery.py`        | FR1          | M          | pending |
| M2-T10 | Consumer signup/verify screens + a11y + locale parity                                                                        | `apps/web/app/(consumer)/**`  | FR1, NFR9/10 | M          | pending |
| M2-T11 | Tests: assurance gating, enumeration uniformity, `prd` stub refusal, recovery revocation, no-PII-in-logs                     | `apps/api/tests/integration/` | FR1, NFR8    | M          | pending |
| M2-T12 | Close the **affiliation four-eyes** gap (a second admin required when a tenant has >1 admin) or record the accepted residual | `identity/affiliation.py`     | FR2          | S          | pending |
| M2-T13 | Observability: `consumer_signup_seconds`, `assurance_transitions_total`, `verification_failures_total`                       | `identity/`                   | NFR13        | S          | pending |

**Acceptance criteria:** a person signs up, verifies both channels, reaches L1 and creates a session; a professional reaches L2 only with licence stub + admin confirmation; enumeration is impossible; the stub channel refuses `prd`; signup p95 < 2 s in the smoke test.
**Validation steps:** `./bin/start.sh test|lint|type`; the signup journey in Playwright; a load smoke for NFR13.
**Rollback:** disable `consumer.signup.enabled` (existing sessions survive); migrations additive.
**Testing requirements:** unit + integration + e2e (signup/verify/recover) + the security rows.

---

### M3 — Consumer record and the public directory (BC8, BC9)

**Objective:** the patient owns a file; the public can find a verified professional; the index contains nothing clinical.
**Scope — in:** master file + children (condition/allergy/occupation with job-safety class), patient-declared provenance, `occupation.changed` event; the directory index + **projection** (allowlisted, one-way), public search/profile pages, listing predicate, visibility controls, delisting, ordering invariant, takedown path.
**Scope — out:** filters beyond free text/specialty (U32), reviews (V2), professional self-service editing, AI matching (M8).
**Dependencies:** M2 (L2 is the listing predicate). **SPECs:** `consumer-onboarding` (§ master file) + `directory-discovery` must be **Approved**.
**Deliverables:** `consumer_record/**`, `directory/**`, `apps/web/app/(public)/directory/**`, `(consumer)/file/**`, migrations for the patient plane and the platform store.
**Complexity:** L · **Operational impact:** the projection job must run (cron/worker) and be monitored for lag.

#### Tasks - M3: consumer record + directory

| ID     | Description                                                                                                                                 | Files                                | FR/NFR       | Complexity | Status  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------ | ---------- | ------- |
| M3-T1  | `master_file` + `condition`/`allergy`/`occupation` in the patient plane, person-scoped, patient-declared provenance                         | `consumer_record/`, `migrations/`    | FR4          | M          | pending |
| M3-T2  | Structured values only where the domain is structured (medication shape, controlled occupation list + free-text "other")                    | `consumer_record/models.py`          | FR4          | M          | pending |
| M3-T3  | `occupation.changed` event + job-safety class mapping (rules consume it in M8)                                                              | `consumer_record/events.py`          | FR4, FR14    | S          | pending |
| M3-T4  | File UI: view/edit, provenance labels, loading/empty/error states, a11y                                                                     | `apps/web/app/(consumer)/file/**`    | FR4, NFR9    | M          | pending |
| M3-T5  | `directory_profile` + `directory_projection_run` schema in the platform store                                                               | `directory/`, `migrations/`          | FR2, FR3     | M          | pending |
| M3-T6  | **Projection job**: field-allowlisted, one-way, classification-tested, audited with counts                                                  | `directory/projection.py`            | FR2, NFR18   | L          | pending |
| M3-T7  | Listing predicate + delisting on assurance/affiliation lapse (audited with reason)                                                          | `directory/eligibility.py`           | FR2          | M          | pending |
| M3-T8  | Public search + profile endpoints, **no session**, rate-limited, cache-friendly                                                             | `directory/api.py`                   | FR3, NFR11   | M          | pending |
| M3-T9  | Public pages: search → results → profile, keyboard-only, indexable, no PHI, no session state                                                | `apps/web/app/(public)/directory/**` | FR3, NFR9/11 | M          | pending |
| M3-T10 | **Ordering invariant** + the sponsored slot (labelled, separate, off by default)                                                            | `directory/ranking.py`               | FR3          | M          | pending |
| M3-T11 | Visibility controls (accepting patients, telehealth, hidden → 404)                                                                          | `directory/visibility.py`            | FR2, FR3     | S          | pending |
| M3-T12 | Takedown: affiliation de-confirmation + operator suppression (audited)                                                                      | `directory/suppression.py`           | FR2          | S          | pending |
| M3-T13 | Tests: schema-has-no-clinical-column, projection fail-closed on unclassified field, ranking invariance under sponsored insertion, delisting | `apps/api/tests/`                    | NFR18        | M          | pending |
| M3-T14 | Observability: `directory_search_seconds`, `directory_projection_lag_seconds`, `directory_delistings_total`                                 | `directory/`                         | NFR11        | S          | pending |

**Acceptance criteria:** an unauthenticated visitor browses seeded profiles; a professional without L2 never appears; a lapsed affiliation delists; **the index schema contains no clinical column (test)**; organically-ranked results are unchanged by adding a sponsored entry; search p95 < 300 ms.
**Validation steps:** `test|lint|type`; the directory e2e + a11y audit; the classification/ordering test suite; projection lag on the dashboard.
**Rollback:** disable `directory.enabled` (public pages 404) and/or `directory.listing.enabled`; the index is rebuildable from the owning stores.
**Testing requirements:** integration (patient plane + platform store) + e2e/a11y + the PHI-freedom and ordering tests.

---

### M4 — Sharing and grants (BC10)

**Objective:** a patient shares their file with a clinician; access is bounded, observable and revocable in seconds.
**Scope — in:** `grant` + `section_registry` + `grant_resolution`, the read-time resolver with sub-5 s caching, revocation + invalidation broadcast, the access log, signed-URL issuance for objects, residency fail-closed.
**Scope — out:** practice→patient UX beyond the mechanism, delegation (never), break-glass (never).
**Dependencies:** M2 (the grantor is an authenticated principal), M3 (there must be a file to share). **SPEC:** `record-sharing` must be **Approved**.
**Deliverables:** `sharing/**`, `(consumer)/file/share|access-log/**`, `(clinician)/patients/[id]/shared/**`, migrations.
**Complexity:** L · **Operational impact:** the resolver is on the hot path for every cross-plane read; a new page-able alert.

#### Tasks - M4: sharing and grants

| ID     | Description                                                                                                                  | Files                                              | FR/NFR     | Complexity | Status  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------- | ---------- | ------- |
| M4-T1  | Versioned `section_registry` (v1: demographics, allergies, medications, conditions) + classification tags                    | `sharing/registry.py`, `migrations/`               | FR5        | M          | pending |
| M4-T2  | `grant` schema + creation rules (no wildcards, bounded expiry, authorised grantor only)                                      | `sharing/grants.py`                                | FR5        | M          | pending |
| M4-T3  | **Read-time resolver** (reader + subject + sections → covered subset from the owning store)                                  | `sharing/resolver.py`                              | FR5, FR6   | L          | pending |
| M4-T4  | Resolution-result cache (TTL **< 5 s**) + revocation + Redis invalidation broadcast                                          | `sharing/resolver.py`, `shared/cache.py`           | FR5, NFR12 | L          | pending |
| M4-T5  | `grant_resolution` audit (sections **ids** only) + the patient-visible access log                                            | `sharing/access_log.py`                            | FR5, FR22  | M          | pending |
| M4-T6  | Consent-vs-grant enforcement (a policy consent missing ⇒ deny)                                                               | `sharing/policy.py`                                | FR5        | S          | pending |
| M4-T7  | Signed-URL issuance for objects after resolution (audited)                                                                   | `sharing/objects.py`, `shared/storage.py`          | FR5, NFR17 | M          | pending |
| M4-T8  | Residency fail-closed path + `grant_denied_total{deny_reason}`                                                               | `sharing/resolver.py`                              | NFR7       | S          | pending |
| M4-T9  | Share + access-log UI (one deliberate action, one-tap revocation, scope legible)                                             | `apps/web/app/(consumer)/**`                       | FR5, NFR9  | M          | pending |
| M4-T10 | Clinician shared-file view: shows **exactly** what the grant allows                                                          | `apps/web/app/(clinician)/patients/[id]/shared/**` | FR6        | M          | pending |
| M4-T11 | Tests: no-access-without-grant, no foreign-plane content persisted, revocation ≤5 s, TTL below budget, no partial disclosure | `apps/api/tests/integration/`                      | NFR12      | L          | pending |
| M4-T12 | Observability + the **grant-revocation-lag page alert**                                                                      | `sharing/`                                         | NFR12      | S          | pending |

**Acceptance criteria:** the demo's J5 works (patient shares → clinician sees only the covered sections → revocation stops access visibly); `grant_revocation_latency_seconds` p95 < 5 s in the test; a cross-plane read without a grant is denied and audited; the access log is patient-only.
**Validation steps:** `test|lint|type`; the sharing e2e; the revocation timing test; a scan for foreign-plane content.
**Rollback:** `sharing.enabled = false` denies all cross-plane reads (fail closed). Revoking grants is the product's own control.
**Testing requirements:** integration across two stores + e2e + the revocation/residency timing tests.

---

### M5 — The practice loop (BC2, BC3, BC4, BC5)

**Objective:** the revision-1 spine, now on real accounts: check-in → redaction → flags → cockpit-lite → AI triage.
**Scope — in:** patients/panel, check-in submission with account sessions (amendment 01 R14–R17), verbatim storage + deterministic redaction, signal rules/attention flags, cockpit read models, the AI triage job (stub provider in the demo), suggestions with provenance + accept/reject/correct, per-tenant AI budget.
**Scope — out:** medication research & matching enablement (staged), FHIR (V2), notifications (V2), scheduling (U11).
**Dependencies:** M1, M2. **SPECs:** `check-in-feedback` (+ amendment 01, already Approved) · `assist-ai` (for the triage job; enablement gated on U15 only for the *staged* jobs, but the SPEC's approval is required for triage too — see §8).
**Deliverables:** `panel/**`, `checkin/**`, `cockpit/**`, `assist/**` (triage only), `(consumer)/checkin/**`, `(clinician)/**`.
**Complexity:** L · **Operational impact:** the loop's metrics become live; the redaction-failure alert becomes meaningful.

#### Tasks - M5: the practice loop

| ID     | Description                                                                                                                                                   | Files                                 | FR/NFR         | Complexity | Status  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | -------------- | ---------- | ------- |
| M5-T1  | `patients` (practice-held) + panel membership + `consents`, tenant-scoped                                                                                     | `panel/`, `migrations/`               | FR7, NFR6      | M          | pending |
| M5-T2  | Check-in intake with **account sessions** (R14–R17): L1 + membership, deep links as entry only                                                                | `checkin/intake.py`                   | FR7            | M          | pending |
| M5-T3  | Verbatim `feedback_items` + deterministic versioned `redacted_text` with fail-closed behaviour                                                                | `checkin/redaction.py`                | FR8, NFR7      | L          | pending |
| M5-T4  | Idempotency by (patient, link, nonce) + validation matrix + effective-adherence derivation in one place                                                       | `checkin/service.py`                  | FR7            | M          | pending |
| M5-T5  | `signal_rules` + `attention_flags` (rules as data, idempotent per window)                                                                                     | `cockpit/rules.py`                    | FR9            | M          | pending |
| M5-T6  | Cockpit-lite read models: panel ordering by attention, 30-day trend per patient                                                                               | `cockpit/read_models.py`              | FR9, NFR1      | L          | pending |
| M5-T7  | AI job transport: Streams + leases/heartbeat + dead-letter; `ai_jobs` as the record                                                                           | `assist/worker.py`, `shared/queue.py` | FR10, NFR3     | L          | pending |
| M5-T8  | Triage job through the **single adapter** with fail-closed redaction verification and provider stub (DeepSeek-shaped)                                         | `assist/provider.py`, `prompts/`      | FR10, NFR7     | L          | pending |
| M5-T9  | Suggestion records (provenance), accept/reject/correct, rejection suppression                                                                                 | `assist/suggestions.py`               | FR10           | M          | pending |
| M5-T10 | Per-tenant AI budget + metering (`ai_tokens_total`/`ai_cost_minor_units`) and pause-on-exhaustion                                                             | `assist/budget.py`                    | NFR15          | M          | pending |
| M5-T11 | Patient check-in + clinician cockpit/triage screens (a11y, 150 KB budget, locale parity)                                                                      | `apps/web/app/**`                     | FR7, NFR2/9/10 | L          | pending |
| M5-T12 | Tests: fail-closed redaction, no-unredacted-egress, provider-input-contains-no-identifiers, AI-output-never-written-to-clinical-tables, job lease/dead-letter | `apps/api/tests/`                     | NFR7           | L          | pending |
| M5-T13 | Observability: loop metrics + the redaction-failure and audit pages                                                                                           | `checkin/`, `assist/`, `cockpit/`     | NFR16          | M          | pending |
| M5-T14 | CSV import for patients + medications (idempotent, dry-run, per-row report) to seed the demo                                                                  | `ingestion/`                          | FR21           | M          | pending |

**Acceptance criteria:** J1/J2/J3 work on the seeded tenant; a redaction failure yields no AI call; a suggestion shows provenance and a label; the loop metric `checkin_to_suggestion_seconds` is populated; cross-tenant read test still green.
**Validation steps:** `test|lint|type`; the loop e2e; load smoke for NFR1/NFR2/NFR3; the fail-closed tests.
**Rollback:** per-tenant flags `checkin.enabled`, `assist.triage.enabled`; queued jobs drain to the dead-letter state.
**Testing requirements:** unit + integration (tenant store + Redis) + e2e + the PHI-egress suite.

---

### M6 — Rx-lite

**Objective:** the demo can show a patient's medication list with history — the seed the staged Sentinel/prescribing work grows from.
**Scope — in:** medication list with drug/dose/start-stop history, structured dose shape, clinician view, patient visibility through the master file and grants.
**Scope — out:** interaction checking, prescribing/finalising, network transmission, refill data (all staged).
**Dependencies:** M3 (master file) + M5 (panel). **SPEC:** **none exists** — M6-T1 authors it (FEATURE_STANDARD §1 requires one).
**Complexity:** M.

#### Tasks - M6: Rx-lite

| ID    | Description                                                                                 | Files                               | FR/NFR    | Complexity | Status  |
| ----- | ------------------------------------------------------------------------------------------- | ----------------------------------- | --------- | ---------- | ------- |
| M6-T1 | **Author the Rx-lite SPEC** (`medication-list`), review, approve — required before any code | `.work/features/medication-list/**` | FR12      | M          | pending |
| M6-T2 | `medication` schema (structured dose, start/stop, source) + migration                       | `panel/`, `migrations/`             | FR12      | M          | pending |
| M6-T3 | API + service for the list/history, tenant-scoped, grant-aware for the patient view         | `panel/medications.py`              | FR12, FR6 | M          | pending |
| M6-T4 | Clinician medication panel + patient file medication section (a11y, locale parity)          | `apps/web/app/**`                   | FR12      | M          | pending |
| M6-T5 | Tests: dose shape validation, history ordering, tenant scoping, grant-covered patient view  | `apps/api/tests/`                   | FR12      | M          | pending |

**Acceptance criteria:** the seeded patient's medication list and history render for both clinician and patient (within grant scope); no interaction logic exists.
**Validation steps:** `test|lint|type`; the Rx-lite e2e.
**Rollback:** flag `rx.lite.enabled`.
**Testing requirements:** unit + integration + e2e.

---

### M7 — Demo hardening, seed data and the acceptance run

**Objective:** the demo is reproducible, seeded, timed, and its acceptance list is executed with evidence — this is the **deliverable**.
**Scope — in:** seed script (one tenant + profiles + one patient), the demo script `S4` timing (≤10 min unaided), the demo acceptance checklist run, a **restore drill**, README/ops notes, the probe re-run for the delivered scope.
**Scope — out:** anything staged.
**Dependencies:** M1–M6.
**Complexity:** M · **Operational impact:** first real end-to-end ops exercise (backup/restore/seed).

#### Tasks - M7: demo hardening

| ID    | Description                                                                             | Files                         | FR/NFR        | Complexity | Status  |
| ----- | --------------------------------------------------------------------------------------- | ----------------------------- | ------------- | ---------- | ------- |
| M7-T1 | Seeded demo tenant + professional profiles + one patient (synthetic only)               | `apps/api/tools/seed_demo.py` | G1            | M          | pending |
| M7-T2 | Demo script: the acceptance list executed step by step with evidence captured           | `.work/reports/`              | G1            | M          | pending |
| M7-T3 | **S4 timing run** (signup → directory → file → grant → clinician views) ≤10 min unaided | —                             | G1, FR1–FR6   | S          | pending |
| M7-T4 | Demo acceptance list executed (doc 01 §Demo acceptance, 6 items)                        | —                             | G1            | S          | pending |
| M7-T5 | Revoked-grant access stop demonstrated (the doc's explicit line)                        | —                             | FR5, NFR12    | S          | pending |
| M7-T6 | **Backup + verified restore drill** across all three stores                             | `bin/start.sh backup          | verify-backup | restore`   | NFR5    |
| M7-T7 | `@plan-foundation probe` re-run for the delivered scope; registries updated             | `.work/plans/**`              | —             | S          | pending |
| M7-T8 | README/ops note for running the demo locally                                            | `README.md`, `.work/docs/`    | G6            | S          | pending |

**Acceptance criteria:** all six demo acceptance items pass on a fresh stack; the S4 journey is timed and under 10 minutes; a restore drill restores all stores and objects; no real data anywhere.
**Validation steps:** `./bin/start.sh --env dev up` → the demo script; `backup`/`verify-backup`/`restore`; the a11y and budget checks.
**Rollback:** the demo stack is disposable; `nuke` + `up` + `seed_demo`.
**Testing requirements:** the full suite green; the demo executed manually with evidence.

---

### M8 — AI routing, Sentinel and the prescribing write path (staged 1st)

**Objective:** the owner-fixed first post-demo increment — Compass matching with tiered gating, deterministic medication-safety alerts, and the in-product prescribing path they gate.
**Scope — in:** routing job + gating predicate + rationale contract + red-flag bypass; the Sentinel deterministic rule engine over a **licensed** data source (adapter + snapshot versioning), occupation×drug rules, clinician-first delivery, cited alerts, override-with-reason + override-rate review; the prescribing write path (opt-in per tenant) with the Sentinel gate before finalisation; the evaluation harness (S5/S6 seeds).
**Scope — out:** network transmission (V3), transcript-aware Sentinel (V3), patient-facing Sentinel copy (until U15).
**Dependencies:** M5 (assist infrastructure), M3/M4 (directory + grants), M6 (medications). **Hard gates:** **U15** (wording + pass bars) and **U30** (drug-data licence) — both must land before **enablement**; the engines can be built against stubs.
**Complexity:** L · **Operational impact:** new provider spend; a licensed-data dependency + a staleness metric.

#### Tasks - M8: routing + Sentinel + prescribing

| ID     | Description                                                                                                                                                                                | Files                                 | FR/NFR         | Complexity | Status  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- | -------------- | ---------- | ------- |
| M8-T1  | `route_patient` job: no-diagnosis output contract + rationale per result                                                                                                                   | `assist/routing.py`, `prompts/`       | FR13, NFR7     | L          | pending |
| M8-T2  | **Gating predicate** (deterministic over the resolved match): in-network self-select · cross-pool + red-flag ⇒ staff confirmation                                                          | `assist/gating.py`, `directory/`      | FR13           | L          | pending |
| M8-T3  | **Red-flag bypass**: exit to emergency guidance with **no** model call; logged as a fact                                                                                                   | `assist/redflag.py`                   | FR13           | M          | pending |
| M8-T4  | Match records (`match_request`/`match_result`) explicitly **not** clinical material                                                                                                        | `assist/matching.py`, `migrations/`   | FR13           | M          | pending |
| M8-T5  | Staff confirmation queue + SLA/auto-expiry for pending cross-pool matches                                                                                                                  | `assist/confirmation.py`, `apps/web/` | FR13           | M          | pending |
| M8-T6  | Directory work the routing exposes: school/network boundary model, richer filters (U32)                                                                                                    | `directory/`                          | FR13           | M          | pending |
| M8-T7  | **Evaluation harness** with the S5 set (≥90% correct specialty, **zero missed red-flags**) and per-job pass bar                                                                            | `apps/api/tools/eval/`                | FR13, G4       | L          | pending |
| M8-T8  | U15 wording package for routing (question, rationale, confirmation notice, non-diagnosis statement) — request + record                                                                     | `.work/reports/`                      | FR13           | S          | pending |
| M8-T9  | Sentinel **deterministic rule engine** (interaction/duplicate/dose/allergy) over a licensed-source adapter + `drug_data_snapshot` versioning                                               | `safety/`, `migrations/`              | FR14           | L          | pending |
| M8-T10 | Occupation × job-safety-class rule set with citations; re-evaluation on `occupation.changed`                                                                                               | `safety/rules/`                       | FR14, FR22     | L          | pending |
| M8-T11 | Alert delivery to the clinician at the point of prescribing + accept/acknowledge/**override with reason** (never a block); override-rate review; the **patient-facing copy staged on U15** | `safety/alerts.py`, `prescribing/`    | FR14, **FR24** | L          | pending |
| M8-T12 | `sentinel_narrative` (AC: phrasing only, rejects decision requests) + staleness metric                                                                                                     | `assist/`, `safety/`                  | FR14           | M          | pending |
| M8-T13 | **Prescribing write path** (opt-in per tenant): draft → final, Sentinel gate, audit, no-network claim in copy                                                                              | `prescribing/**`, `migrations/`       | FR15           | L          | pending |
| M8-T14 | S6 evaluation (zero missed high-severity hits, cited) + the enablement gates wired to `evaluation_runs`                                                                                    | `apps/api/tools/eval/`                | FR14, G4       | M          | pending |
| M8-T15 | Tests: no-diagnosis scan, gating predicate matrix, red-flag bypass asserts no provider call, deterministic-alert-origin, override logged and non-blocking                                  | `apps/api/tests/`                     | FR13/14        | L          | pending |
| M8-T16 | Enable `research_medication` for real use: citations required, **"unverified — no source"** when the provider returns none, evaluation bar before enablement                               | `assist/`, `apps/api/tools/eval/`     | **FR11**, G4   | M          | pending |

**Acceptance criteria:** routing returns matches + rationales and never a diagnosis; the gating predicate behaves per the owner's rule; a red flag never reaches the model; Sentinel alerts cite their basis and overrides are logged; **no job type is enabled until its harness passes and U15 signs the wording**.
**Validation steps:** `test|lint|type`; the S5/S6 harness runs; the override-rate dashboard review.
**Rollback:** per-job-type flags (all off by default, gated on `evaluation_runs`); the prescribing write path is per-tenant opt-in.
**Testing requirements:** unit + integration + the evaluation harness + manual clinical-wording review (U15).

---

### M9 — Practice self-service (staged 2nd)

**Objective:** a practice onboards itself: invitations, roles, subscription.
**Scope — in:** invitations (staff + patients), roles/permissions, subscription shape (U12 informs pricing, not architecture), tenant admin console basics.
**Dependencies:** M2 (identity), M12 for SSO. **Gate:** U12 for the billing model's *terms*, not for the mechanism.
**Complexity:** M–L.

#### Tasks - M9: practice self-service

| ID    | Description                                                                                 | Files                                     | FR/NFR     | Complexity | Status  |
| ----- | ------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------- | ---------- | ------- |
| M9-T1 | Author/review the practice self-service SPEC                                                | `.work/features/practice-self-service/**` | FR18       | M          | pending |
| M9-T2 | Invitation flow (staff + patients) reusing identity verification                            | `identity/invitations.py`                 | FR18       | M          | pending |
| M9-T3 | Roles/permissions model + enforcement points                                                | `identity/roles.py`                       | FR18, NFR6 | M          | pending |
| M9-T4 | Subscription/plan record + per-tenant feature flags (billing provider integration deferred) | `platform/billing.py`                     | FR18       | M          | pending |
| M9-T5 | Tenant-admin console (members, roles, plan)                                                 | `apps/web/app/(clinician)/admin/**`       | FR18       | M          | pending |
| M9-T6 | Tier promotion path (practice → enterprise) documented and tested                           | `platform/`, `bin/start.sh`               | FR20       | M          | pending |

**Acceptance criteria:** a practice invites a clinician and a patient, assigns roles, and sees its plan; tier promotion is exercised in a test.
**Validation steps:** `test|lint|type`; the admin e2e.
**Rollback:** flags per tenant; additive migrations.
**Testing requirements:** integration + e2e.

---

### M10 — Live telehealth and recording (staged 3rd)

**Objective:** a real clinician↔patient video visit from the chart, with resilience, and opt-in recording to the owning store.
**Scope — in:** the ADR 009 vendor adapter, ephemeral tenant-scoped rooms, short-lived single-participant tokens, browser join, waiting room + device check, audio-only fallback + dial-in, join/leave audit, recording lifecycle (opt-in per session with consent, 7-year lifecycle, tenant/patient-plane storage via ADR 015), media NFRs.
**Dependencies:** M3/M4 (records + grants), M2 (participant identity); **hard gate U29** (vendor + BAA) and **U33** (storage service) for the real thing.
**Complexity:** L · **Operational impact:** a new sub-processor; object storage in the backup story; media cost.

#### Tasks - M10: live telehealth

| ID      | Description                                                                                                      | Files                                    | FR/NFR      | Complexity | Status  |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------- | ---------- | ------- |
| M10-T1  | Author the Live SPEC (rooms, tokens, resilience, recording consent)                                              | `.work/features/live-visits/**`          | FR16        | M          | pending |
| M10-T2  | Vendor adapter port (`shared`-style interface, provider-agnostic) + a stub implementation for tests              | `live/vendor_adapter.py`                 | FR16        | L          | pending |
| M10-T3  | Room lifecycle: per-encounter, tenant-scoped, ephemeral, destroyed after                                         | `live/rooms.py`                          | FR16        | M          | pending |
| M10-T4  | Per-participant short-lived tokens; Care Circle limited tokens (when that ships)                                 | `live/tokens.py`, `identity/`            | FR16, NFR7  | M          | pending |
| M10-T5  | Waiting room + device/connection check + audio-only and dial-in fallbacks                                        | `apps/web/app/**`, `live/`               | FR16, NFR14 | L          | pending |
| M10-T6  | Recording lifecycle: opt-in per session, consent recorded, objects to the owning plane, **signed-URL access**    | `live/recording.py`, `shared/storage.py` | FR16, NFR17 | L          | pending |
| M10-T7  | Backup/RPO/RTO extended to objects; `verify-backup` covers them                                                  | `bin/start.sh`, `shared/storage.py`      | NFR5, R33   | L          | pending |
| M10-T8  | Join/leave audit + `live_*` metrics + media-degradation telemetry                                                | `live/`                                  | FR22, NFR14 | M          | pending |
| M10-T9  | In-chart embed (start from the patient's chart, never a separate app) + recap into the timeline                  | `apps/web/app/(clinician)/**`            | FR16        | M          | pending |
| M10-T10 | Tests: token scope, room teardown, audio-only fallback path, recording consent gating, no vendor default storage | `apps/api/tests/`                        | FR16        | L          | pending |

**Acceptance criteria:** a visit starts from the chart; a phone joins in the browser with no install; audio survives a bandwidth drop; a dial-in path exists; recording is off by default and, when enabled, lands only in the owning store with a lifecycle rule.
**Validation steps:** the media NFR smoke on a real vendor sandbox (U29); restore drill including objects.
**Rollback:** flag `live.enabled`; recording flag off by default; the adapter makes a vendor swap a configuration change.
**Testing requirements:** integration + adapter contract tests + a manual media test.

---

### M11 — Virtual pharmacy partner (staged 4th)

**Objective:** prescriptions reach a licensed partner; **Mendarion never dispenses**.
**Scope — in:** partner integration boundary (I5), refill/adherence data ingestion where the partner offers it, and the V3 e-prescribing network adapter (**designed, not enabled**).
**Dependencies:** M8 (prescriptions exist), M4 (grants for any PHI movement). **Gate:** partner selection + licence terms.
**Complexity:** M.

#### Tasks - M11: pharmacy partner

| ID     | Description                                                                                      | Files                                   | FR/NFR | Complexity | Status  |
| ------ | ------------------------------------------------------------------------------------------------ | --------------------------------------- | ------ | ---------- | ------- |
| M11-T1 | Author the pharmacy-partner SPEC (boundary only; never dispense)                                 | `.work/features/pharmacy-partner/**`    | FR17   | M          | pending |
| M11-T2 | Partner adapter port + a stub; no dispensing logic may exist anywhere in the codebase (asserted) | `ingestion/` or `prescribing/partners/` | FR17   | M          | pending |
| M11-T3 | Refill/adherence ingestion into the patient's medication view (grant-scoped)                     | `panel/`                                | FR17   | M          | pending |
| M11-T4 | E-prescribing network adapter **interface** (unimplemented, V3) + audit hooks                    | `prescribing/network.py`                | FR17   | S          | pending |

**Acceptance criteria:** a test asserts no dispensing/stock/fulfilment code path exists; the partner boundary is an adapter with a documented contract.
**Validation steps:** `test|lint|type`; a code scan for dispensing logic.
**Rollback:** the integration is inert until a partner is configured.
**Testing requirements:** adapter contract tests + the no-dispensing scan.

---

### M12 — Enterprise/hospital tier and pilot readiness (staged, unsequenced by the owner)

**Objective:** the enterprise tier (ADR 011/009) and everything the pilot needs that the demo does not.
**Scope — in:** dedicated isolation for enterprise tenants (own database set + storage boundary), optional **dedicated media** configuration, SSO (V3), extended audit, stricter residency; **CI** (U2); the compliance pack (U13/U14/U15 outcomes, DPAs/BAAs); load testing at pilot volume; the Redis keep/remove review (U19).
**Dependencies:** M10; **hard gates U13, U14** and the owner's residency decision.
**Complexity:** L · **Operational impact:** the largest ops change in the plan.

#### Tasks - M12: enterprise tier + pilot readiness

| ID     | Description                                                                                                                    | Files                             | FR/NFR           | Complexity | Status  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- | ---------------- | ---------- | ------- |
| M12-T1 | Enterprise tier provisioning: dedicated database set + storage boundary + residency placement                                  | `platform/`, `bin/start.sh`       | FR19, NFR4       | L          | pending |
| M12-T2 | **CI pipeline** (GitHub Actions): lint, type, unit+integration, migration idempotency, OpenAPI diff, MOD-06 record             | `.github/workflows/`              | R20              | L          | pending |
| M12-T3 | Enterprise SSO (OIDC/SAML) + extended audit views                                                                              | `identity/sso.py`, `platform/`    | FR19             | L          | pending |
| M12-T4 | Dedicated media configuration for enterprise tenants (ADR 009 §8)                                                              | `live/`, `platform/`              | FR19, NFR14      | M          | pending |
| M12-T5 | Compliance pack: U13 residency/retention windows, U14 vendor contracts, U15 sign-offs, DPAs/BAAs, the data-processing register | `.work/docs/`                     | NFR17            | L          | pending |
| M12-T6 | Load test at pilot volume (1 clinic, 10 clinicians, 5k patients) with NFR assertions                                           | `apps/api/tools/`                 | NFR1–3, NFR11–13 | L          | pending |
| M12-T7 | Redis keep/remove review (U19) with hit-rate + job-queue evidence                                                              | —                                 | R18              | S          | pending |
| M12-T8 | Patient-plane capacity note (the P3 review's named seam) + connection-budget plan                                              | `.work/reports/`                  | NFR4             | M          | pending |
| M12-T9 | Incident runbooks + on-call/alerts finalisation; the SMB pool ADR if tenant count justifies it                                 | `.work/docs/`, `.work/decisions/` | G6               | M          | pending |

**Acceptance criteria:** an enterprise tenant is provisioned with dedicated isolation and passes the same isolation tests; CI runs every gate; the compliance pack is complete and reviewed; the pilot load targets are met or the gaps are recorded with owners.
**Validation steps:** CI green on `main`; the load-test report; the compliance-pack review; the restore drill at the new scale.
**Rollback:** tier provisioning is reversible by re-provisioning (documented copy → verify → cutover).
**Testing requirements:** CI + load + isolation tests for the enterprise shape.

---

## 20. Acceptance Criteria (global)

- **The demo:** all six items of doc 01 §Demo acceptance pass on a fresh seeded stack, with evidence, and the S4 journey is timed ≤10 minutes unaided. (M1–M7)
- **Isolation:** a cross-tenant read and a cross-plane read without a grant both return zero rows in every test suite; RLS is present in every tenant DB. (NFR6)
- **PHI discipline:** no un-redacted egress; no PII/PHI in telemetry; the public index has no clinical column. (NFR7/NFR8/NFR18)
- **Sharing:** revocation effective ≤5 s, measured; the access log is patient-only. (NFR12, FR5)
- **AI discipline:** provenance on every output; no autonomous clinical write; each job type enabled only after its evaluation bar. (G4)
- **Operability:** every routine operation is a control-plane verb; a verified restore drill covers all stores and objects. (G6, NFR5)
- **Staged honesty:** no shipped copy claims a capability that has not been built (no network prescribing claim before V3; no patient-facing Sentinel copy before U15).

## 21. Validation Gates

| Gate                         | Command / action                                  | Applies to                                 |
| ---------------------------- | ------------------------------------------------- | ------------------------------------------ |
| Unit + integration           | `./bin/start.sh test`                             | every task                                 |
| Lint                         | `./bin/start.sh lint`                             | every task                                 |
| Types                        | `./bin/start.sh type`                             | every task                                 |
| Web tests + e2e              | `./bin/start.sh web-test` · `npm run e2e`         | every UI task                              |
| Migration idempotency        | `./bin/start.sh migrate` twice                    | any migration                              |
| Stack + health               | `./bin/start.sh --env dev up` → `status`/`health` | M1+, every milestone                       |
| Production preflight         | `./bin/start.sh --env prd smoke`                  | any deployment-shape change (M1, M10, M12) |
| Backup/restore               | `backup` → `verify-backup` → `restore`            | M1, M7, M10, M12                           |
| Security assertions          | the named security tests (§17)                    | M1, M2, M3, M4, M5, M8                     |
| Media smoke (vendor sandbox) | manual, per ADR 009                               | M10                                        |
| Evaluation harness           | `apps/api/tools/eval/` per job type               | M5 (triage), M8 (routing, Sentinel)        |
| Compliance review            | owner + CTO collaborator                          | M8 (U15), M12 (U13/U14)                    |
| Scope gates                  | `touch-scope-verify.sh` · `blast-radius-check.sh` | every task                                 |
| MOD-06                       | concept run, output attached                      | every agent-authored code task             |

## 22. Rollback and Recovery Considerations

<mark>Developer Notes:  Verify the rollback and recovery considerations.</mark>

- **Feature flags are the primary rollback:** every new surface ships behind one (`consumer.signup`, `directory[.listing|.sponsored]`, `sharing[.residency.strict]`, `checkin`, `assist.*`, `rx.lite`, `live`, prescribing-per-tenant). Their **fail-closed directions** are documented (e.g. `sharing.enabled=false` denies all cross-plane reads).
- **Migrations are additive and idempotent**; a breaking change is two-step (expand → migrate → contract). Destructive statements require same-message owner approval and a documented plan (`.cursorrules` §Database).
- **The directory index and the projections are rebuildable** from the owning stores — a rollback path that data in a tenant store does not have.
- **Store-level recovery:** per-store backups + verified restore (NFR5); a restore drill is a **milestone acceptance item**, not an afterthought (M7-T6).
- **The tenant is disposable in the demo:** `nuke` → `up` → seed.
- **Per-milestone rollback** is recorded in each milestone block above.

## 23. Technical Debt Prevention Strategy

<mark>Developer Notes: Prevention of technical debt is critical -> Preventing technical debt in AI code development centers on making implicit AI decisions explicit and enforceable before generation happens. The core mechanisms include: **spec-driven development** that defines function signatures, expected inputs/outputs, edge cases, performance constraints, and which existing utilities to reuse before asking the AI to implement; **context engineering** that feeds the agent your architecture context — interface contracts, linter config, ADRs, and relevant module functions — so it imports existing helpers instead of cloning them; **contract enforcement** via machine-checkable schemas (Pydantic, Zod, OpenAPI) that turn assumptions into runtime-validated contracts and block drift at CI; **architectural boundary enforcement** through ALLOWED_IMPORTS-style rules that fail builds when generated code crosses service or module boundaries; **duplication prevention** via AST-based clone detection in every PR (blocking blocks of 5+ duplicated lines) and a "do we already have this?" habit before generation; **traceability** through living specs that maintain bidirectional linkage between intent and implementation so divergence triggers a build failure rather than silently accumulating; and **governance practices** such as reserving 15–20% sprint capacity for refactoring, tracking a refactor-to-add ratio, running quarterly architecture reviews, and requiring human review of any AI-authored architectural or security-boundary code.  The underlying principle is that AI embeds 10–30 unstated assumptions per feature — spanning dependency versions, schema formats, error-handling, concurrency, and integration contracts — and each unaddressed assumption compounds with every subsequent change, so the highest-leverage prevention is bounding those assumptions at the input layer (specs, contracts, context) rather than only reviewing outputs.</mark>

- **Refactor pressure points (named now, not later):** (a) `shared/planes.py` + `shared/db.py` will accumulate plane logic — keep them interface-only and tested; (b) the grant resolver's cache correctness is a privacy-critical coupling — the TTL-invalidation invariant is asserted, not assumed; (c) the projection mapper is the boundary that keeps the public store PHI-free — every added field needs a classification review; (d) the AI prompt/output contract grows per job type — keep `prompts/` versioned and immutably referenced by suggestions.
- **Debt ledger policy:** debt is recorded as a `RISK_REGISTRY` entry or a SPEC open question with an owner — never as a code comment alone. A milestone cannot close with an unowned `TODO` in `src/`.
- **The demo-divergence policy:** every demo shortcut (mock verification, no CI, stub provider, minimal UI) is recorded with the milestone that replaces it — so "temporary" has an end date.
- **No drive-by refactors:** `.cursorrules` forbids collateral edits; scope is declared per task.

## 24. AI-Agent Execution Guidance

- **Read before writing:** `.cursorrules` → `DIRECTORY_MAP` §2/§3 → the SPEC for the context → `CONVENTIONS` → the observability spec for the signals.
- **Dangerous paths (require explicit care and a test):** `shared/{db,tenancy,planes}.py` (isolation), `sharing/resolver.py` (read-time resolution + revocation), `checkin/redaction.py`, `directory/projection.py`, `bin/start.sh` + compose (protected files — same-message owner approval required), anything under `migrations/`.
- **Never:** write AI output into a clinical table; bypass the tenancy/plane resolver; create a second egress point for a provider; add a clinical column to the platform store; commit without an explicit instruction; run destructive DB operations without same-message approval.
- **Model-tier hints:** **strong** for M1-T5/T6 (isolation + control plane), M4-T3/T4 (resolver/revocation), M5-T3/T7/T8 (redaction, job transport, adapter), M8-T2/T9/T11 (gating predicate, rule engine, prescribing gate); **standard** for the remaining context work; **light** for docs, locale files, seed scripts and test scaffolding.
- **Per-task contract:** restate the applicable R-rules, list the files, run the milestone's validation commands, attach the MOD-06 output for code, and report failures verbatim.
- **Sequencing rule:** never start a task whose SPEC is not Approved; never enable a job type whose evaluation bar has not passed.

## 25. Long-Term Maintainability Strategy

<mark>Developer Notes: **Model-drift handling is absent.** The single biggest unique risk in AI-assisted development is that the model changes over time (new version, different tool, updated system prompt) and produces *different* code for the *same* spec. Your section needs an explicit rule: **the spec is the source of truth; generated code is compiled output.** When a model update or tool change produces divergent output, the fix is to recompile from the spec (or regenerate the affected slice), never to hand-patch the generated code and let it drift from the intent.  Without this, every model upgrade silently rewrites architectural assumptions, and your ADRs become stale relative to what the code actually does. Pair this with a **prompt/spec version pin** — record which model version and which spec revision produced each merged slice, so you can reproduce or diff against a known-good baseline.</mark>

<mark>Developer Notes: **Test debt is invisible in your review cadence.** You review dependencies, alerts, and the U19 cache quarterly, but tests are the *executable contracts* that make the whole system enforceable. If tests rot — flaky, over-mocked, slow, or silently skipped under deadline pressure — the contract layer degrades silently and every other safeguard (CI gates, architecture checks, duplication detection) loses its teeth. Add a **test-health review** to the quarterly cadence: flake rate, coverage drift on critical paths, and a "test that never fails" sweep (a test that has passed without ever being red is either redundant or too weak).</mark>

- **Ownership:** one developer (owner) for now; every context has a named package and a service interface, so a second developer can be added per-context without archaeology.
- **Documentation upkeep:** ADRs are the decision record (never edited once Decided — superseded or amended by a new file); SPECs are amended, never rewritten; the registries are append-only histories.
- **Deprecation policy:** a superseded ADR keeps its file and gets a `Superseded by` status; a superseded SPEC keeps its file; the foundation docs are versioned by date prefix.
- **Review cadence:** architecture fitness review at each phase gate and before each staged milestone; the threat model is re-reviewed whenever a data flow changes; the observability spec is re-reviewed when a metric never triggers an action (deleted, not kept).
- **Quarterly (or per-milestone):** the U19 cache review, the alert-quality review (false-positive rate), and the dependency/security review.

---

## Appendix A — Decision log

| ID  | Date       | Choice                                                                                                                                                                                   | Alternatives rejected                                                                                                           |
| --- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| D1  | 2026-09-25 | **Twelve milestones**: M1–M7 = the demo, then the owner-fixed staged order (M8 routing+Sentinel+prescribing → M9 self-service → M10 Live → M11 pharmacy) with the enterprise tier at M12 | One mega-milestone (unreviewable); feature-ordered milestones that break the owner's staging; putting the enterprise tier first |
| D2  | 2026-09-25 | **No advanced mode applied** (balanced default); the demo's speed bias is handled by explicit scope cuts per milestone                                                                   | `startup` mode (would loosen gates the compliance surfaces need); `enterprise` mode (over-processes a 2-week demo)              |
| D3  | 2026-09-25 | **A separate M1 skeleton milestone** that lands three stores + the extended control plane before any feature                                                                             | Folding infra into M2 (would hide the revision's real ops cost — R13/MOD-04 — until late)                                       |
| D4  | 2026-09-25 | **`medication-list` SPEC authored as M6-T1** rather than implementing Rx-lite without one                                                                                                | Implementing Rx-lite without a SPEC (violates FEATURE_STANDARD §1)                                                              |
| D5  | 2026-09-25 | **Enablement gates wired to `evaluation_runs` + U15** for routing and Sentinel (build against stubs, enable only on evidence)                                                            | Shipping the engines enabled and adding the harness later (R24/R30 are H/H)                                                     |
| D6  | 2026-09-25 | **Recording + object storage + backup coverage in the same milestone (M10)**, not a follow-up                                                                                            | Shipping recording first and "doing backups later" (R33)                                                                        |
| D7  | 2026-09-25 | **CI deferred to M12**, with per-task validation commands in the interim                                                                                                                 | Adding CI in M1 (real cost for a 2-week demo; U2 is an owner/eng decision)                                                      |
| D8  | 2026-09-25 | **Demo UI falls back to a minimal in-house component set** if `@ui-bootstrap` does not land in time, with the divergence recorded                                                        | Blocking the demo on the UI Design OS (R19 would become a hard stop)                                                            |

## Appendix B — Traceability matrix (goal → FR → ADR → SPEC → task → test → acceptance)

| Goal                      | FR               | ADR                       | SPEC                                                                                                  | Task(s)               | Test                                                                                                                                                      | Acceptance                                   |
| ------------------------- | ---------------- | ------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| G1 demo                   | FR1–FR12         | 011–014 (+006 superseded) | consumer-onboarding · directory-discovery · record-sharing · check-in-feedback(+a1) · medication-list | M1–M7                 | the milestone suites + the demo script                                                                                                                    | all six demo items pass, S4 ≤10 min          |
| G2 record ownership       | FR4–FR6          | 011, 014                  | record-sharing                                                                                        | M3-T1, M4-T1…T12      | `test_no_access_without_grant`, `test_no_foreign_plane_content_persisted`, `test_demo_revoked_grant_stops_clinician_access`                               | revocation ≤5 s measured                     |
| G3 trustworthy discovery  | FR2, FR3         | 012, 013                  | directory-discovery                                                                                   | M3-T5…T14             | `test_listing_requires_active_l2_and_affiliation`, `test_index_schema_has_no_clinical_column`, `test_organic_ranking_invariant_under_sponsored_insertion` | index PHI-free; ordering payment-independent |
| G4 advisory AI            | FR10, FR13, FR14 | 007, 016, 017             | assist-ai(+a1)                                                                                        | M5-T7…T13, M8-T1…T15  | `test_ai_output_never_written_to_clinical_tables`, `test_red_flag_bypasses_model_and_confirmation`, `test_sentinel_alert_origin_is_deterministic`         | every job type gated on its evaluation bar   |
| G5 pilot targets          | FR7–FR11         | 002, 003, 005             | check-in-feedback · assist-ai                                                                         | M5                    | the loop metrics + load smoke                                                                                                                             | S1–S3 measurable                             |
| G6 one-person operability | FR20, FR22       | 008, 011                  | —                                                                                                     | M1-T6/T13, M7-T6, M12 | `backup`/`verify-backup`/`restore`                                                                                                                        | every op is a control-plane verb             |
| Staged: routing/Sentinel  | FR13–FR15        | 010, 016, 017             | assist-ai(+a1)                                                                                        | M8                    | S5/S6 harness                                                                                                                                             | U15 + U30 gates                              |
| Staged: self-service      | FR18             | 012                       | practice-self-service                                                                                 | M9                    | admin e2e                                                                                                                                                 | invitation/role/plan flow                    |
| Staged: Live              | FR16             | 009, 015                  | live-visits                                                                                           | M10                   | media NFR smoke                                                                                                                                           | U29 + U33 gates                              |
| Staged: pharmacy          | FR17             | 010                       | pharmacy-partner                                                                                      | M11                   | no-dispensing scan                                                                                                                                        | partner-only                                 |
| Staged: enterprise        | FR19             | 011, 009                  | —                                                                                                     | M12                   | isolation tests + load                                                                                                                                    | U13 gate                                     |

## Appendix C — Registries reference

- `.work/plans/ASSUMPTIONS.md` (A1–A38) · `.work/plans/RISK_REGISTRY.md` (R1–R33) · `.work/plans/UNKNOWNS.md` (U1–U34)
- Foundation: `.work/plans/foundation/20260924-01-mendarion-initial-scope.md` (rev 2) · `20260924-04-foundation-architecture.md` (rev 2) · `20260924-02-integration-resources.md` · `PROBE_LEDGER.md` (iteration 9, coverage 90%)
- Decisions: `.work/decisions/README.md` (ADRs 001–017) · SPECs: `.work/features/**` · Standards: `.work/standards/**`

## Next action

The **plan owner reviews this plan** and sets `Status: Approved` (or returns it with amendments). Until then it is **Proposed / under review** and broad implementation is forbidden. After approval: `@plan-master status` (scores **implementation-ready**) → `@session-control start` → `@code-implementation plan - M1`, once the M1 dependencies' protected-file approvals (M1-T6) and the M1–M5 SPEC approvals are in place.
