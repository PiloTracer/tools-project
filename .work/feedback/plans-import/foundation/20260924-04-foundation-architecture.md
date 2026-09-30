# Mendarion — foundation architecture (doc 04)

**Doc:** foundation **04** (architecture foundation — *not* the master plan) · **Created:** 2026-09-24 · **Phase:** P1
**Status:** **Revision 2 APPLIED** 2026-09-24 — this doc now describes the **multi-segment product** (professionals, clinics, patients/consumers, hospitals) of doc 01 rev 2 + concept revision 2. Revision 1 (the practice-side slice, accepted 2026-09-24) is kept as the demo's spine and as the record. Applied here: §2 = demo milestone + owner-fixed staged order; §3 = the revision-2 context set (BC1–BC13, each labelled demo/staged; **BC14 added 2026-09-27 by ADR 020**); §5 = the accepted revision-2 NFRs; §6 = the new entities (master record, grants, directory, occupation, Live, Sentinel, prescribing); §10 = the P2 queue for the revision.
**ADRs:** 001–006, 008, 009, 010, **011–020 Decided**; 007 **Proposed** (U15). **Needs:** nothing for the foundation; U13/U15/U29–U33 stay open with owners, and **U42** (who authors/translates tenant copy) is open for the customization SPEC.

> This document is the **architecture foundation**: bounded contexts, dependency direction, NFR targets, provisional data model and the P2 decision queue. The master implementation plan (`*-full-plan.md`) is authored later by `@plan-master`.

---

## 1. Purpose and constraints carried from P0

- Product intent, personas, capabilities, scope and success criteria: `.work/plans/foundation/20260924-01-mendarion-initial-scope.md` (doc 01).
- Binding constraints: **1 developer** (operator 2026-09-24) · **the 2-week build is the demo milestone** (D-S3) · beside-EHR with **one read-only import path** — and, from ADR 010, a **prescribing write path that is opt-in per tenant** · **global market, EN + ES** · **AI assist layer**, advisory only, anything leaving our boundary redacted first (ADR 005) · **segments = professionals, clinics, patients/consumers, hospitals** (A30) · **release tiers ≠ build order** (A33).
- Three invariants are non-negotiable (concept rev 2 §7–§8): tenant scoping enforced **at the data-access layer**; **raw PHI never crosses a tenant boundary** or enters the PHI-free platform layer (which now also hosts the **public directory index**); and **every cross-store read goes through an explicit consent grant** (A28/U22 — no snapshot copies).

## 2. Delivery scope: the demo milestone + the owner-fixed staged order (revision 2)

**The 2-week synthetic demo is milestone 1** (D-S3, U28) and keeps the revision-1 loop as its spine. Everything past it is ordered by the owner (2026-09-24) — the concept's MVP/V2/V3 labels are **release tiers, not build order** (A33).

| # | Demo milestone (2 weeks, synthetic) | Staged order (owner 2026-09-24) |
|---|-------------------------------------|--------------------------------|
| 1 | **Practice loop** (revision-1 spine, unchanged): patient check-in → clinician Cockpit-lite → AI feedback triage, on one seeded tenant | — |
| 2 | **Consumer core**: public signup (mock verification) → practitioner directory browse → patient master file → **one share grant** → the clinician opens the shared file | Compass filters/matching (§3 BC9) and verified reviews = V2 tier |
| 3 | **Rx-lite** (medication list, start/stop/dose history) | interaction/duplicate flags + **Sentinel** = **1st after the demo**, with AI routing |
| 4 | **AI routing (Compass matching)** | **1st after the demo** — mandatory-confirmation rule for cross-pool matches, red-flag path, evaluation set (U23/R24) |
| 5 | **Prescribing write path** (per-tenant opt-in, ADR 010) | **1st after the demo**, with Sentinel — the alert is *at the point of prescribing*; network transmission = **V3** |
| 6 | **Practice self-service** (invitations, roles, subscription) | **2nd** |
| 7 | **Live (telehealth visits)** — managed vendor via the ADR 009 adapter, browser join, opt-in recording to tenant storage | **3rd** |
| 8 | **Virtual pharmacy** (partner-only — U25 closed) | **4th** |
| 9 | **Hospital / enterprise tier** (dedicated isolation, SSO, extended audit, dedicated media) | not sequenced by that decision |

**Out of scope for the demo** (kept explicit): real identity verification (U27's assurance levels ship with the milestone that needs them), live AI vendor calls, telehealth, pharmacy, recording, peer benchmarking, Medication Digital Twin, Care Circle (**incl. as a Live participant** — concept §4.8 describes it but §12 puts it at V2; the roadmap governs), FHIR import, e-prescribing network, multi-location Org.

**Divergences recorded, not silent:** D2 → EN-first (revision 1, unchanged); concept MVP line vs the demo → the demo is a subset and the rest is staged in the order above; deliverable = **internal demo on synthetic data** (U16) so production auth, consent capture at production strength, vendor BAAs and the incident path are out of the demo — while the tenant/PHI schema, grants and audit are built because they cost nothing now and avoid a pilot-time rewrite.

## 3. Bounded contexts (revision 2 — each labelled by delivery phase)

| Id | Context | Owns | Phase | Notes |
|----|---------|------|-------|-------|
| BC1 | **Identity & Access** | Staff **and consumer/patient** accounts, sessions, roles, **assurance levels** (contact-verified patient; **licence + affiliation-verified professional** — U27), MFA for clinicians | demo (accounts) · staged (verification) | ADR 006 **superseded** (patients hold real accounts); enterprise SSO = V3 |
| BC2 | **Patient & Panel** | The patient record **as a practice holds it** (its own captured demographics + practice-owned clinical parts), panel membership, consent flags, enrolment from a Compass match | demo | PHI-heavy; consent is a stored fact, not a checkbox |
| BC3 | **Check-in & Feedback** | Check-in capture, adherence tap, symptom/mood score, feedback item (+ its redacted twin) | demo | The Loop's write path; owns redaction before AI |
| BC4 | **Cockpit & Signals** | Computed trends, threshold rules, attention flags | demo | Read-model; no PHI duplication beyond entitlement |
| BC5 | **Assist (AI)** | **The single egress port**: redaction orchestration, provider calls, suggestion/match/alert inference records with provenance, accept/reject/override capture | demo (triage) · staged (routing, Sentinel narrative) | Advisory only; MOD-07 / MOD-03 |
| BC6 | **Ingestion** | CSV import; FHIR/HL7 adapter interface; **e-prescribing adapter interface** (unimplemented) | demo (CSV) | Import stays **read-only**; the prescribing write path is BC13 (ADR 010) |
| BC7 | **Platform Ops** | Tenant registry + **tier attribute**, seed/config, feature flags, PHI-free telemetry, **public directory index hosting** | demo | Command/Org consoles stay out of the demo |
| BC8 | **Consumer Record (master file)** | The **patient-owned** master record: demographics, conditions, allergies, medications, documents, **occupation + job-safety class**; survives practice changes | demo (basic fields) · staged (documents, imports) | The patient is the owner; practices read/write their own parts (BC2) |
| BC9 | **Directory & Discovery (Compass)** | PHI-free professional/clinic profiles + the public searchable index, filters, **AI matching orchestration** (via BC5) with rationale, verified aggregate reviews | demo (seeded profiles + browse) · staged (filters, matching, reviews) | Browsable **without an account**; matching is never a diagnosis (R31) |
| BC10 | **Sharing & Grants** | Bilateral, scoped, time-boxed, revocable grants; **read-time resolution**; grant audit | demo (one grant) · staged (scopes, expiry UX, revocation audit) | **The only path between stores**; no snapshot copies (U22) |
| BC11 | **Live (Telehealth)** | Visit rooms + the ADR 009 vendor adapter, per-participant short-lived tokens, waiting room/device check, recording lifecycle (opt-in, tenant storage), join/leave events | staged (3rd) | Human-blocking on U13/U29 for real patients |
| BC12 | **Safety (Sentinel)** | The **deterministic** rule engine + licensed drug-data lookups, occupation×drug rules, alerts + **override records**, citations | staged (1st) | Advisory, clinician-first; never a silent block (R30) |
| BC13 | **Prescribing (Rx)** | Prescriptions (draft → final), the Sentinel gate call, override logging, the e-prescribing adapter port (V3) | staged (1st, per-tenant opt-in) | ADR 010; a real write path, bounded to this context |
| BC14 | **Configuration & Customization** (added 2026-09-27, ADR 020) | The tenant's **versioned definitions** — vocabularies, forms/questionnaires, workflow statuses & steps, rule sets, templates & copy, reminder plans, role compositions, branding — plus the **extension-point catalogue** and the **resolver**; publish/approve lifecycle with four-eyes | T0 foundations at **M1** (nothing rendered) · capability at **M9** · safety-rule authoring at **M8** · enterprise cascade at **M12** | **The only context that is read-only for every other context** (resolve only) and **forbidden from reading clinical data**: definitions here, evaluation in the owning context via the pure `shared/rules.py` (ADR 020 §4). Tenant store; follows the tenant's placement (ADR 018) |

## 4. Dependency direction and data planes (revision 2)

- **Clinical flow (unchanged):** `BC6 Ingestion → BC2 Patient & Panel → BC3 Check-in & Feedback → BC4 Cockpit & Signals`; `BC3 → BC5 Assist` (asynchronous, after redaction). `BC4` never calls `BC5` synchronously — suggestions arrive as data the clinician pulls, so an AI/Redis outage degrades nothing clinical.
- **Discovery flow (new):** `BC9 Directory & Discovery` is **public** (no session) and reads only the PHI-free index in the platform store; `BC9 → BC5` for matching inference only — the ranking rationale is returned with the result (R31), and a red-flag presentation exits to emergency guidance instead of matching. Enrolment: `BC9 → BC1` (account + assurance) `→ BC2` (panel link).
- **Sharing flow (new):** **every** cross-store read passes `BC10 Sharing & Grants` — the patient's master file (`BC8`) and each practice's own parts (`BC2`) are separate stores; a grant is resolved at read time so revocation is immediate (U22). No context reads another store directly, and no snapshot copies exist.
- **Visit flow (new):** `BC11 Live → BC1` (participant identity + assurance for tokens), `BC11 → BC2/BC8` (links the session to the encounter; recording references land with the encounter's owner), `BC11 → BC7` (join/leave audit events). The vendor adapter sits **inside** BC11 (ADR 009) — no other context talks to the media vendor.
- **Prescribing flow (new):** `BC13 Prescribing → BC12 Safety` *before* finalisation (advisory: accept / acknowledge / **override with reason**), `BC12 → BC5` only for narrative phrasing — the interaction rules themselves come from the **licensed drug-data source**, never from a general model (R30/U30). `BC13 → BC6` is the e-prescribing adapter port (V3).
- **Customization flow (new, ADR 020):** `any context → BC14` **read-only** (`resolve(tenant, extension_point, scope)` → the definition version + merged payload, with a platform default when the tenant authored nothing). `BC14 → any clinical context` is **forbidden**: the definition lives in BC14, the **evaluation** happens in the owning context through the pure `shared/rules.py`. `BC14 → BC7` reads entitlements and the canonical vocabulary only, and writes no definition body into the PHI-free plane (SPEC R5). Adding a customization to a new functionality is a catalogue entry + a resolver call + an import contract — never new machinery.
- **Data planes (three, not two):** **tenant store** (PHI: BC2/BC3/BC4 + practice-owned parts) · **patient plane** (PHI, patient-owned: the BC8 master file and its objects, with BC10 as the only gate) · **platform store** (PHI-free by design: BC7 config/telemetry/registry + the **public directory index**). Cross-plane traffic carries grants, aggregates or de-identified text only, enforced in the data-access layer with RLS as defence-in-depth.
- **Tenancy shape:** practice and enterprise **tiers** (U21) are a first-class mutable tenant attribute; the enterprise tier gets dedicated isolation and may get dedicated media (ADR 009). The **physical shape of the patient plane** (a dedicated consumer store vs a "home tenant" holding the master file) is an open decision → **U34** / the ADR 002 amendment.
- **AI sub-processor:** one egress port (BC5) for every model call — triage, routing, Sentinel narrative; the contract is U14, redaction is fail-closed (ADR 005), and transcripts (V3) keep the same rule.

## 5. NFR targets (accepted by the owner 2026-09-24 — proposed as stated/assumed)

Every row is either **stated** (operator said it) or **assumed** (professional baseline for a pilot-scale clinical SaaS, proposed for confirmation). Numbers, not prose.

| Area | Target | Basis |
|------|--------|-------|
| Performance — clinician Cockpit | p95 < 1.5 s for panel + 30-day trend; p99 < 3 s | assumed (dashboard use, pilot scale) |
| Performance — patient check-in | submit p95 < 1 s on a 4G phone; interaction budget "seconds, not minutes" (concept 4.4) | stated (concept) + assumed |
| AI suggestion latency | p95 < 30 s from check-in to suggestion visible; failure is silent-degrade to "no suggestion" | assumed |
| Availability | 99.5% monthly for the pilot; **AI provider outage must not degrade clinical flows** | assumed |
| Durability / recovery | nightly encrypted backups, RPO ≤ 24 h, RTO ≤ 4 h (slice); 1 h/15 min when the paid pilot starts | assumed |
| Scale (pilot) | 1 clinic, ≤ 10 clinician users, ≤ 5k patients, ≤ 50k check-ins/year → volume class **K–M rows** per tenant | stated (slice) + assumed volume |
| Security | per-tenant database + RLS; MFA for clinicians; **patient/consumer accounts with contact verification** (short-lived tokens replace magic links); **professional licence + affiliation verification before directory listing** (U27); encrypt at rest and in transit; PHI access audit log incl. **grant and video join/leave events** | stated (concept rev 2 §8) + U27 decision |
| Privacy | explicit granular consent per sharing feature **and per grant**; export + erasure workflow documented; retention per tenant policy (default **7 years** for clinical records **and recordings**, which are opt-in per session — U31); recording **off by default** | stated (concept rev 2 §8) + U31 decision |
| i18n / l10n | 2-week build ships **EN** with locale-file structure; **ES** is the next slice | accepted amendment of D2 (owner 2026-09-24) |
| Accessibility | WCAG 2.2 AA for the patient check-in flow, AA-targeted for the Cockpit | assumed |
| Cost | AI unit cost modelled per tenant (MOD-03) with a per-tenant spend cap; target AI spend ≤ 5% of per-seat revenue | assumed (R15) |
| Observability | structured logs with ids only (no PHI), request tracing across BC3→BC5, alert on AI error-rate and on redaction-step failures | stated (`.cursorrules` §no PII in logs) |
| **Live — media** (rev 2) | 720p target, audio survives degradation (drop video < ~1 Mbps), one-way latency < 300 ms; **automatic audio-only + dial-in fallback**; device/connection check before the waiting room | owner-accepted 2026-09-24 |
| **Live — isolation** (rev 2) | enterprise tenant may use a **dedicated media configuration**; recordings never leave the tenant store | ADR 009 · owner-accepted |
| **Availability — enterprise tier** (rev 2) | **99.9%** monthly (practice tier stays 99.5%) | owner-accepted 2026-09-24 |
| **Directory** (rev 2) | public search p95 < 300 ms; index is PHI-free | owner-accepted 2026-09-24 |
| **Sharing** (rev 2) | grant revocation effective ≤ 5 s (read-time resolution, no copies to invalidate) | owner-accepted · U22 |
| **Consumer onboarding** (rev 2) | signup p95 < 2 s; the Compass→share journey completable unaided in ≤ 10 min (S4) | owner-accepted · S4 |

## 6. Data model (provisional — entities, volume class, sensitivity)

| Entity | Key relationships | Volume class (pilot) | Sensitivity / PII fields |
|--------|-------------------|----------------------|--------------------------|
| `tenant` | 1—N everything clinical (slice: exactly 1) | 1–10 | internal config |
| `staff_user` | N—1 tenant; N—N panel | 10–100 | **PII**: name, email, phone, professional licence number |
| `patient` (practice-held parts) | N—1 tenant (a person may be a patient of **several** tenants); 1—N check-in, medication, encounter; linked to the master file by **grant** | 1k–10k | **PHI**: what *this* practice captured; the master file is BC8 |
| `encounter` | N—1 patient | 10k–100k | **PHI**: date, reason, clinician notes |
| `medication` | N—1 patient | 10k–100k | **PHI**: drug, dose, start/stop dates (prescribing data) |
| `checkin` | N—1 patient | 100k–500k/yr | **PHI**: adherence, symptom/pain/mood scores, timestamp |
| `feedback_item` | N—1 check-in; 1—1 redacted twin | same as check-in | **PHI**: free text (highest-risk field in the product) |
| `redacted_text` | 1—1 feedback_item | same | derived; treated as *reduced*, not de-identified |
| `ai_suggestion` | N—1 check-in/patient; N—1 model run | 1 per triaged item | derived from redacted text; stores model id, prompt hash, output, provenance, accept/reject |
| `signal_rule` / `attention_flag` | N—1 tenant / N—1 patient | tens / thousands | internal (may embed clinical meaning — treat as PHI) |
| `consent` | N—1 patient (or consumer) | per patient | **PII/PHI**: consent type, timestamp, revocation — incl. **recording consent** (U31) |
| `consumer_account` / `identity_assurance` | 1—1 person; assurance level | 1 per person | **PII**: contact details, verification state; professionals: **licence number + verification + affiliation** (U27) |
| `master_file` + `condition` / `allergy` / `document` / `occupation` | owned by the person; referenced by grants | per person | **PHI** (occupation/job-safety class drives Sentinel rules — U26) |
| `grant` | grantor ↔ grantee (person ↔ practice/clinician), scope, expiry, revocation | tens–hundreds per person | metadata + PHI pointers; **no copies**; audited (U22/BC10) |
| `directory_profile` / `verified_review` | N—1 professional; N—1 completed encounter | tens–thousands | **PHI-free** by construction (platform store); reviews are aggregates tied to real visits (R31) |
| `match_request` / `match_result` | N—1 consumer; N—1 model run | 1 per enquiry | rationale stored; **never a diagnosis**; not clinical record material (BC9/BC5) |
| `live_session` / `session_participant` / `recording_ref` | N—1 encounter; 1—N participants | 1 per visit | **PHI** metadata; recordings are **C4-v objects in tenant storage** (ADR 009/U31) |
| `prescription` | N—1 patient; N—1 encounter; 1—N `sentinel_alert` | 10k–100k | **PHI** prescribing data; write path opt-in per tenant (ADR 010) |
| `sentinel_alert` + `override` | N—1 prescription or medication review | 1 per flagged item | alert basis, rule version, **override reason** (R30); knowledge base = licensed data source (U30) |
| `drug_data_snapshot` | N—1 per release | per release | licensed dataset version + age (staleness is a safety signal) |
| `audit_event` | append-only, all contexts | M rows/yr | no clinical content: actor, resource id, action, timestamp |

Retention, erasure and residency for these rows are blocked on **U13** (jurisdiction + residency placement) — which now also governs **where recordings and the patient-plane store may live**; the audit log is append-only and never pruned. The physical shape of the patient plane is **U34**; the object-storage service for recordings is **U33** (ADR 003's trigger has fired).

## 7. Assist (AI) layer — design rules carried into architecture

1. **Advisory only:** suggestions are stored as `ai_suggestion` records, shown with provenance, never written into clinical fields, never sent to a patient (R11).
2. **Redact before egress:** BC3 produces `redacted_text` before BC5 calls any provider; original text never leaves the tenant store (A15). Redaction failure ⇒ no AI call (fail closed), and the failure is logged without content.
3. **Provenance + audit:** every suggestion records model id, prompt version hash, input reference and the source items it was derived from; clinician accept/reject is captured and feeds the S3 metric and the evaluation set.
4. **Cost & failure:** per-tenant spend cap, batching where possible, cache medication lookups, degrade silently when the provider is down (R14/R15).
5. **Concept ids:** run **MOD-07** (prompt composition) when the AI feature SPEC is opened and **MOD-03** (billable unit) in the AI ADR; `prompt.md` outputs attach to the SPEC/ADR, not here.
6. **Routing (Compass matching) — new:** the model returns specialties/professionals **with a plain-language rationale**, never a diagnosis; cross-pool matches may require staff confirmation (U23) and a red-flag presentation bypasses matching entirely (R24/R31). Match results are not clinical record material.
7. **Sentinel — new:** interactions/duplicates/dose-range/allergy checks come from a **licensed clinical drug-data source** with cited evidence, not from a general model's output (U30); the model is used only for narrative phrasing into the clinician's and (later, U15-gated) patient's language. Alerts are advisory: accept / acknowledge / **override with a documented reason**, every override logged — **never a silent block** (R30).
8. **Clinician-first rule stays:** no AI output reaches a patient without the professional acting first — the routing suggestion (U23) and the patient-facing Sentinel copy (staged) are the two recorded exceptions, both gated by U15 wording sign-off.

## 8. Integration posture (detail in doc 02)

| Integration | Posture | Owner question |
|-------------|---------|----------------|
| **I1** FHIR/HL7 read-only import | interface designed, implementation deferred → CSV in the demo | U7 (closed), U17 |
| **I2** CSV import | in the demo | — |
| **I3** AI model provider | **DeepSeek** via the BC5 adapter, redaction-in-layer first; agreement open | U14 |
| **I4** e-prescribing network | **V3**; the BC6 adapter port is designed but unimplemented | U13 |
| **I5** Pharmacy refill/dispensing | **partner-only — Mendarion never dispenses** (owner 2026-09-24); partner selection before the pilot | U25 (**closed**), R25 |
| **I6** Enterprise SSO | V3 (enterprise tier) | U21 |
| **I7** Telehealth video vendor | **managed HIPAA-eligible WebRTC behind the BC11 adapter** (ADR 009); BAA + residency are gates | **U29** |
| **I8** Licensed drug-interaction data source | required by Sentinel before it ships; never a general model | **U30** |
| **I9** Dial-in telephony | with Live; the video vendor if it offers it, else a voice vendor | U29 |
| **I10** Transcription | **V3** (transcript-aware Sentinel v2); keeps the ADR 005 egress rule | U31 |

## 9. Traceability

| Requirement | Where it is honoured |
|-------------|----------------------|
| Success criteria S1–S3 (doc 01 §Success criteria) | S1 ← BC4 signals + `attention_flag`; S2 ← check-in/adherence data + `ai_suggestion` accept/reject; S3 ← `ai_suggestion` accept rate |
| Tenant + PHI invariants (concept §5–§6) | §4 data planes + data-access-layer scoping |
| AI is advisory only (A14) | §7 rule 1 + R11 |
| Retire R12 (residual PHI) | §7 rule 2 + U14 |
| 1 developer / 2 weeks (A12) | §2 demo milestone, R13/R16/R28 |
| **Compass** — public discovery + matching (concept §4.7, R31) | §3 BC9 + §4 discovery flow + §7 rule 6 + S5 |
| **Live** — telehealth visits (concept §4.8, ADR 009) | §3 BC11 + §4 visit flow + §5 media NFRs + R29/R33 |
| **Sentinel** — medication safety (concept §5, ADR 010) | §3 BC12/BC13 + §6 alert entities + §7 rules 7–8 + S6 + R30 |
| **Prescribing write path** (ADR 010) | §3 BC13 + §4 prescribing flow + R32 |
| **Consumer onboarding** (S4) | §3 BC1/BC8/BC9/BC10 + §5 onboarding NFR |
| Recording consent + retention (U31) | §5 privacy row + §6 `recording_ref` + R33 + U33 |

## 10. Decisions needed (P2 — answered 2026-09-24: ADRs 001–006 **Decided**, 007 **Proposed** awaiting the CTO collaborator)

1. **Backend stack** (`p2-backend`) — one language, minimal moving parts for a solo maintainer.
2. **Database + data services** (`p2-database`, `p2-data-services`) — Postgres as the only store in the slice (cache/queue/search all `none` **earned** by the K–M volume class, or justified by the AI async path).
3. **Hosting + tenancy operation** (`p2-hosting`, `p2-tenancy`) — hosting *shape* decided by ADR 004; region stays deferred (U13).
4. **AI provider + contract** (ADR 005; U14) — with MOD-03 cost estimate.
5. **Frontend shape** (`p2-frontend`) — one responsive app vs separate patient app for the slice.

All five are drafted as ADRs **001–006** in `.work/decisions/`, plus **007** for the AI advisory-only posture (needs the CTO collaborator's sign-off, U15). Each carries its evidence-derived recommendation and the alternatives that were rejected; an owner decision flips it to **Decided**. Companion interaction `p2-locales` needs no ADR: language scope was already fixed by D2 + A11.

**Revision-2 P2 queue (opened 2026-09-24 — the ADRs the consumer re-baseline requires):**

| # | Decision | Why it cannot be skipped | Owner input |
|---|----------|--------------------------|-------------|
| R2-1 | **Amend ADR 002** for the two tiers (practice + enterprise) **and the patient plane** (U34: dedicated consumer store vs home tenant) | ADR 002 currently fixes practice-as-tenant as the only shape; the revision adds a patient-owned master file and cross-practice access | owner (tenancy change) + `p2-tenancy` |
| R2-2 | **Supersede ADR 006** (magic links, no patient accounts) | patients/consumers now hold real accounts with assurance levels (U27) | `p2-frontend` + ADR 001/006 review |
| R2-3 | **New: consumer identity + directory** (assurance levels, public index, listing eligibility) | R27 (impersonation), the PHI-free index boundary, and the directory's business rules ("never pay-for-rank", §11) | `p2-tenancy`/`p2-frontend` |
| R2-4 | **New: record sharing & grants** (bilateral grants, read-time resolution, revocation, audit) | U22's "no snapshot copies" is architectural, not a UI detail | `p2-database` |
| R2-5 | **Revisit ADR 003 for object storage** — trigger **fired** by recordings (U31/U33) | recordings are C4-v objects in tenant storage; backups/RPO/restore change (R33) | `p2-data-services` |
| R2-6 | **New: AI routing posture** (extends ADR 007: gating rule, red-flag path, rationale, no-diagnosis wording) | R24 regulated triage; patient-facing output is the exception ADR 007 did not anticipate | owner + U15 (CTO) |
| R2-7 | **New: safety alerting** (deterministic rules, licensed data source, override semantics, clinician-first) | R30; the alert is a clinical-safety artefact and its wording is a claims question | owner + U15 |

ADR **009** (telehealth delivery) and **010** (prescribing surface) were already decided by the owner on 2026-09-24 and are not re-opened here.

**Queue status 2026-09-25 — all seven rows are drafted as ADRs, one per row, each with an evidence-derived recommendation and its rejected alternatives; the owner ratified the batch as Decided the same day (the P2 gate for the revision is therefore closed):**

| # | ADR | Outcome |
|---|-----|---------|
| R2-1 | [011](.work/decisions/20260925-011-tenancy-tiers-and-patient-plane.md) | Two tiers as a first-class `tier` attribute; **patient plane = dedicated consumer store** (U34 answered by the owner 2026-09-25); amends 002 |
| R2-2 | [012](.work/decisions/20260925-012-identity-and-access-model.md) | Real consumer/staff accounts + assurance levels (L0/L1/L2) + global identity with per-membership access; supersedes 006's magic-link patient access, **retains** one app + i18n + a11y |
| R2-3 | [013](.work/decisions/20260925-013-practitioner-directory.md) | PHI-free public index in the platform store; browsable at L0; listing gated on L2; **placement never above clinical fit**; verified aggregates only (U32 → V2 filters) |
| R2-4 | [014](.work/decisions/20260925-014-record-sharing-and-grants.md) | BC10 is the only path between stores; bilateral scoped grants resolved at read time; no copies; §5's ≤5 s revocation met by state change + explicit invalidation |
| R2-5 | [015](.work/decisions/20260925-015-object-storage.md) | Objects live inside their owner's plane; signed-URL access; 7-year lifecycle retention; supersedes 003's storage deferral; **service selection Deferred → U33** |
| R2-6 | [016](.work/decisions/20260925-016-ai-routing-posture.md) | Match, never a diagnosis; **tiered gating confirmed by the owner 2026-09-25**; red flags bypass AI entirely; extends 007 with one recorded exception to rule 1 |
| R2-7 | [017](.work/decisions/20260925-017-safety-alerting-sentinel.md) | Deterministic rules over a licensed drug-data source (never a general model); clinician-first; cited basis; override with reason, never a silent block; S6 enablement gate |

Blockers carried by the new ADRs, all with owners: **U13** (jurisdiction/residency — gates the enterprise tier, the patient plane's placement, the licence registry and the media/vendor residency), **U29** (telehealth vendor), **U30** (licensed drug-data source), **U32** (Compass data dependencies), **U33** (object-storage service), **U15** (patient-facing wording + evaluation pass bars). **U34 is closed.** ADR 007 stays Proposed pending U15 and is now *extended* by 016 rather than replaced.

**Downstream consequence (P3, not P2): the two merged SPECs need amendments.** They were written for the revision-1 identity model and are **not** edited in place (SPEC rule: amendments, never merged edits):

| # | SPEC | Pending amendment |
|---|------|-------------------|
| R2-8 | `.work/features/check-in-feedback/20260924-SPEC.md` (**Approved**) | R1/R2 + the `/v1/checkins` contract and the threat note still describe **single-use magic-link patient access**; revision 2 replaces this with **consumer/patient accounts** (ADR 006 supersession, U27 assurance) while keeping the check-in itself unchanged. Until the amendment lands, the SPEC and doc 01 rev 2 disagree — **recorded here, not silently left** |
| R2-9 | `.work/features/assist-ai/20260924-SPEC.md` (**Approved** 2026-09-26, with the U15 carve-out on the R7 claims wording + R12 pass bar; its amendment 01 is Approved the same day) | Scope grew: routing (Compass matching) and Sentinel narrative join the three original jobs, with the clinician-first rule, the licensed drug-data source (U30) and the override semantics (ADR 010) |

## 11. Decisions register (synced with `.work/decisions/`; ADRs win on conflict)

| # | ADR file | Topic | Status |
|---|----------|-------|--------|
| 001 | `20260924-001-backend-stack.md` | Backend stack — Python 3.12 + FastAPI | **Decided** — **its interpreter pin is amended by 019** (Python **3.14** + upgrade policy); the stack choice (FastAPI + Pydantic v2 + SQLAlchemy 2.x) stands |
| 002 | `20260924-002-database-and-tenancy-operation.md` | Database + tenancy — PostgreSQL, DB per tenant, RLS inside each | **Decided** — practice tier stands; **amended by 011**; **its "Alembic migrations" tooling sentence is superseded by plan §11 / ADR 019 §Decision 3** — the migration path is numbered idempotent SQL applied per store by `mendarion.shared.migrate` (one path, no second tool) |
| 003 | `20260924-003-data-services.md` | Data services — Redis (cache + Streams); search engine + object storage deferred | **Decided** (divergence R18/U19) — storage deferral **superseded by 015**; Redis decisions unchanged |
| 004 | `20260924-004-hosting-and-region.md` | Hosting — Fly.io-class, single region | **Decided** — region Deferred → U13 |
| 005 | `20260924-005-ai-provider-and-redaction-boundary.md` | AI provider + redaction boundary | **Decided** — vendor/contract Deferred → U14 |
| 006 | `20260924-006-frontend-and-i18n.md` | Frontend — one Next.js + TS app; EN now / ES next | **Decided** — one app/i18n/a11y retained; **magic-link patient access superseded by 012** |
| 007 | `20260924-007-ai-advisory-only-posture.md` | AI advisory-only posture + clinical-claims boundary | **Proposed** — needs CTO sign-off (U15); **extended by 016** |
| 008 | `20260924-008-two-environment-docker-stack.md` | Two-environment Docker stack (`dev` / `prd` suffix scheme) + `bin/start.sh` control plane; supersedes the single-environment P5 files | **Decided** 2026-09-24 (owner directive) |
| 009 | `20260924-009-telehealth-delivery.md` | Telehealth delivery — managed HIPAA-eligible WebRTC behind an internal adapter; ephemeral tenant-scoped rooms; recordings to tenant storage | **Decided** 2026-09-24 (approach) — **vendor Deferred** → U29 |
| 010 | `20260924-010-prescribing-surface.md` | Prescribing — in-product write path, opt-in per tenant; e-prescribing **network** stays V3; Sentinel advisory-only with logged override | **Decided** 2026-09-24 (owner) — amends D3's read-only reading for prescribing |
| 011 | `20260925-011-tenancy-tiers-and-patient-plane.md` | Tenancy — practice tier + **enterprise/hospital tier**; **patient plane = dedicated consumer store** (U34); `tier` is a first-class attribute | **Decided** 2026-09-25 (P2 batch, owner-ratified) — amends 002 |
| 012 | `20260925-012-identity-and-access-model.md` | Identity — consumer/staff accounts, assurance levels L0/L1/L2, global identity + per-membership access, staff MFA, recovery in scope | **Decided** 2026-09-25 (P2 batch, owner-ratified) — supersedes 006's magic-link access |
| 013 | `20260925-013-practitioner-directory.md` | Directory (Compass) — PHI-free public index in the platform store, L0 browse, L2 listing, placement never above clinical fit, verified aggregates | **Decided** 2026-09-25 (P2 batch, owner-ratified) — U32 Open |
| 014 | `20260925-014-record-sharing-and-grants.md` | Sharing — BC10 the only path between stores; bilateral scoped grants at read time; no copies; ≤5 s revocation; full lifecycle audit | **Decided** 2026-09-25 (P2 batch, owner-ratified) |
| 015 | `20260925-015-object-storage.md` | Object storage — objects inside their owner's plane; signed URLs; 7-year lifecycle retention | **Decided** 2026-09-25 (P2 batch, owner-ratified) — supersedes 003's deferral; **service Deferred → U33** |
| 016 | `20260925-016-ai-routing-posture.md` | AI routing — match not diagnosis; tiered gating (self-select in-network; staff confirmation cross-pool + red flags; red flags bypass AI); evaluation + wording gates | **Decided** 2026-09-25 (P2 batch, owner-ratified) — extends 007 |
| 017 | `20260925-017-safety-alerting-sentinel.md` | Sentinel — deterministic rules over a **licensed** drug-data source; clinician-first; cited; override with reason; never a silent block; S6 gate | **Decided** 2026-09-25 (P2 batch, owner-ratified) — **U30 Open**; patient copy staged on U15 |
| 018 | `20260926-018-hybrid-tenant-store-placement.md` | Tenancy placement — hybrid: schema-isolated RLS pool for practice/SMB, dedicated DB/instance for enterprise/compliance-sensitive; placement is a tenant-registry attribute; scale-out schema conventions binding from M1 | **Decided** 2026-09-26 (owner, developer-notes review) — amends 002's pool deferral and 011's practice-tier row; pool rollout pre-pilot (M12-T13) |
| 019 | `20260926-019-python-interpreter-pin.md` | Interpreter — **Python 3.14** with a binding upgrade policy (re-pin within one minor of its `.1`; re-validate at every phase gate) | **Decided** 2026-09-26 (owner; confirmed the same day) — **amends 001's interpreter pin**; supersedes 002's "Alembic" tooling sentence (one migration path via `mendarion.shared.migrate`); 3.13 is the recorded fallback, never 3.12 |
| 020 | `20260927-020-tenant-customization-model.md` | Customization — **BC14** with versioned tenant definitions (JSONB body inside a relational envelope; **no separate document store**), declared **extension points** + one resolver, closed vocabularies, four-eyes publish, tighten-only Sentinel, canonical-core/tenant-extension | **Decided** 2026-09-27 (owner: "proceed with all recommendations" — D-A…D-G of the customization proposal accepted) — corrects plan `M12-T11`'s single override-store wording; **no new store**; SPEC `customization` **In review** |

**Gate note:** P2 requires stack, hosting and tenancy ADRs **Decided** and database/data-services **Decided or Deferred** — satisfied for the practice-side set on 2026-09-24, and for the revision the tenancy ADR is **011** (U34 answered by the owner 2026-09-25); the P2 batch 011–017 was **ratified as Decided on 2026-09-25**, so the gate holds. ADR 007 is a compliance-posture record whose blocker is documented (U15); it does not gate P3 for non-AI SPECs. ADR 008 was added after P6 (owner directive, 2026-09-24) and supersedes the P5 single-environment artifacts named in `DOCS_TECH_STACK.md` §3.

## 12. Foundation-ready gate (P1) — PASSED 2026-09-24 (revision 1) · **re-run for revision 2 the same day**

- [x] Owner confirms the §2 slice (U17) and the §5 NFR defaults — "Accept doc 04 §2 as written" + "Accept the proposed defaults"
- [x] Deliverable type settled (U16): internal demo on synthetic data
- [x] `p1-data-model` recorded (§6 + doc 01 §Data model) — entities, volume class, PII labels; exercised for real at `p2-database`
- [x] Doc 02 written for the import path + AI provider posture (vendor mirrors deferred with owners — no vendor fixed yet)
- [x] Doc 01 §Data model cross-linked to §6; doc 03 deliberately skipped (no adjacent module in the slice)
- [x] Registries synced (U16/U17 closed, U11 closed for the slice, R16/R17 mitigated, A11 amended, A20 added)
- [x] No unresolved contradictions between doc 01 scope, this doc and the registries — the D2 divergence is recorded, not silent

**Revision-2 re-run (2026-09-24):**

- [x] Doc 04 carries the revision-2 bounded contexts (BC1–BC13, phase-labelled) and the dependency direction for all six flows · **BC14 added 2026-09-27 by ADR 020** (customization — tenant-definition store, extension points, resolver; tenant store; no clinical reads)
- [x] `p1-nfr` — the revision-2 NFRs (media, resilience, enterprise availability, directory, sharing, onboarding, recording) are **owner-accepted** and now recorded here in §5, not only in doc 01
- [x] `p1-data-model` — the new entities (§6) are drafted with volume class + sensitivity/plane; **U34** carries the one physical-shape question (patient plane) — **closed 2026-09-25: dedicated consumer store** (ADR 011)
- [x] `p1-integrations` — I7–I10 recorded with owners (U29/U30/U31/U32); **U25 closed** (partner-only)
- [x] Owner answers recorded in this phase: **U27** (contact-verified patients, licence/affiliation-verified professionals) · **U25** (partner-only, never dispense) · **U31** (opt-in per session, 7-year retention, tenant object storage)
- [x] Cross-links: doc 01 ↔ doc 02 ↔ doc 04 (doc 03 adjacency still deliberately skipped — no adjacent module)
- [x] Registries synced: U25/U27/U31 closed, U24 closed earlier, **U33/U34 opened**, R29–R33 live, A31–A34 recorded
- [x] No **unrecorded** contradiction: the D3/BC6 amendment (ADR 010), the ADR 006 supersession and the ADR 002 amendment are recorded as pending P2 work (R2-1/R2-2), and the one live divergence — the **Approved `check-in-feedback` SPEC still specifies magic-link patient access** — is recorded here as **R2-8** with a P3 amendment queued

**P2 gate (revision 2) — PASSED 2026-09-25.** The revision-2 queue R2-1…R2-7 is resolved as **ADRs 011–017**, all **Decided** and owner-ratified (see §10 and §11): stack/hosting/tenancy are Decided (001/004/011), database/data-services Decided with the object-storage service Deferred to **U33** (002/003/015), and ADR 007's blocker stays documented (U15). The P3 amendments **R2-8/R2-9** are the remaining downstream consequence and are the next P3 work.

## Next action

`@plan-foundation continue` — **P3: the SPEC set.** P2's revision-2 queue is resolved (ADRs 011–017 Decided; U34 closed by the owner). P3 stages the SPEC set to the **demo milestone**: amendments **R2-8** (`check-in-feedback` → consumer accounts) and **R2-9** (`assist-ai` → routing + Sentinel scope), plus new SPECs for the demo's consumer core (signup/assurance, directory browse, master file, one grant). Then the revised **P6** re-certifies `plan-master-ready`, which is what un-gates `@plan-master greenfield`.
