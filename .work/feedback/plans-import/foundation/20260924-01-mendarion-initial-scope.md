# Mendarion — Initial exploration and scope

**Doc:** foundation **01** (P0 product-intent capture) · **Created:** 2026-09-24 · **Phase:** P0 · **Project name:** Mendarion (repo + GitHub slug: `mendarion`)
**Source concepts (owner-authored, do not edit):** `.work/prompts/Meridian — Practice Intelligence & Patient Connection OS (1).html` (**revision 2 — CURRENT**: Eight pillars, adds *Compass*, *Live*, *Sentinel* and the Telehealth approach) · `.work/prompts/Meridian — Practice Intelligence & Patient Connection OS.html` (revision 1 — the historical record; superseded where the two disagree) · covering note: `.work/prompts/telehealth - ammendment.md`. The concept filenames themselves still read "Meridian" because they are owner-authored files we do not edit (see A32).
**Product name:** **mendarion** (renamed from Meridian by owner directive 2026-09-24; repo + GitHub slug already `mendarion`).
**Status:** **Revision 2 — COMPLETE 2026-09-25** (owner steer 2026-09-24: the product serves **professionals, clinics, patients/consumers and hospitals**, not only practices) · Revision 1 (practice-side slice) closed 2026-09-24; revision 2 supersedes it wherever the two disagree · **Needs:** nothing from the foundation — the P0/P1 grills are answered and the consequences are decided in **ADRs 011–017**: **U27** (identity assurance → ADR 012) · **U24/U25** (telehealth + pharmacy posture → ADR 009; partner-only) · **U31/U34** (recording; patient plane → ADR 015/011). Carried with owners: U6/U12/U13/U14 (priority, business model, jurisdiction, AI vendor) and U15 (patient-facing AI wording + evaluation pass bars, internal CTO collaborator) — none blocks the demo. The **P0 product grill is answered** (U21/U22/U23/U26/U28 closed 2026-09-24).

---

## Revision 2 (2026-09-24) — multi-segment product scope (CURRENT)

**Trigger:** the owner's consumer-platform steer, captured verbatim with the impact map in `.work/plans/proposals/20260924-consumer-platform-steer.md`. Decisions: **D-S1a** re-baseline v1 · **D-S2** hybrid identity/tenancy · **D-S3** the 2-week synthetic demo stays the first milestone. Product-grill answers: **U21** two tenancy tiers · **U22** bilateral grant model · **U23** tiered AI-routing gating · **U26** patient-declared occupation, clinician-first warnings · **U28** demo = practice loop + minimal consumer path.
**Second trigger (same day): the owner's concept revision 2** (Eight pillars; adds **Compass**, **Live**, **Sentinel**; §6 telehealth approach; updated compliance/roadmap/risk/business/tech sections). Absorbed here: the named pillars below, the prescribing **write path** (**ADR 010** — amends the read-only reading of D3), the telehealth approach (**ADR 009**), and three owner rulings on the drifts: the **build order stands** (the concept's MVP/V2/V3 are **release tiers**, not build order — A33), **prescribing in-product now / network at V3**, and **Sentinel stays clinician-first** (so the concept's patient-facing warning copy is *staged* until U15 signs the wording, not dropped).

### Named pillars from concept revision 2 (vocabulary adopted)

| Concept pillar | Maps to capability rows | Note |
|----------------|------------------------|------|
| **Compass** (§4.7) | rows 2 (directory) + 6 (AI matching) + consumer enrollment | New: **public, searchable directory without an account**; filters incl. specialty/condition/location/telehealth availability/language/insurance accepted/next available slot; AI matching returns a ranked shortlist **with a plain-language rationale, never a diagnosis**; self-service enrollment from a match with **inline identity verification + consent capture**; per-professional visibility/capacity controls; reviews are **verified aggregates tied to completed visits**, never open free-text |
| **Live** (§4.8) | row 8 (virtual meetings) | Provider-initiated from the chart or patient-initiated inside a scheduling window; one-tap browser join; waiting-room device check; visit links to the encounter; recap feeds Closer/Health Timeline; prescribing actions flow to Rx Radar → Sentinel (ADR 010) |
| **Sentinel** (§5) | row 10 (medication/occupation warnings) | Cross-cutting layer, not a screen: physician alert **at the point of prescribing** with evidence (interaction, duplicate therapy, dose range, condition/allergy), acknowledge/**override with a documented reason**/accept — **never a silent block**; patient copy in Closer (staged, see above); inputs = full regimen (Rx Radar), self-reported OTC/supplements (The Loop), chart allergy/condition data, and — **V3 only** — an opt-in disclosed visit transcript; guardrails: decision support (not diagnostic/prescribing authority), every alert cites its basis, overrides logged, and the interaction knowledge base is a **licensed clinical drug-data source, never a general-purpose model's unverified output** (U30) |

**Release tiers (concept rev 2 §11/§12) vs build order:** the concept's *MVP* includes tenant provisioning, Cockpit, Rx Radar, The Loop, Closer, basic Org **and Live**; *V2* adds benchmarking, Medication Digital Twin, Care Circle (**including as Live participants**), multi-location Org, FHIR import, **Compass** and **Sentinel v1**; *V3* adds the e-prescribing network, pharmacy refill data, the enterprise dedicated-database **and dedicated-media** tier, SOC 2 Type II, the dashboard builder and **Sentinel v2 (transcript-aware)**. Owner ruling: these are **release tiers, not build order** — the milestone order stays as decided (AI routing + medication-safety alerts → practice self-service → live telehealth → pharmacy). Business model (§11): Solo/Small = Live + Compass listing per seat; Clinic/Group adds Org; Enterprise adds dedicated DB + **dedicated media**; Compass placement terms may never rank above clinical fit.

### Who it is for (revision 2)

| Segment | Who | What they get | Tenancy |
|---------|-----|---------------|---------|
| **Prospective consumer** (new in rev 2) | anyone, **before** enrolling — the concept's "Prospective Patient / Consumer" | **public directory search without an account** (Compass §4.7), AI matching to specialties/professionals with a rationale, self-service enrollment with inline identity verification + consent | no account yet; platform-level (PHI-free) |
| **Consumer / patient** | any person (public signup) | own account and **master record**, browse the practitioner directory, ask a symptom question to find the right physician, complete a file and share it with any doctor, medication warnings, join a live video visit | global identity (not tenant-bound) |
| **Practitioner / clinician** | solo doctor or clinician inside a clinic or hospital | cockpit-lite stats, patient list, AI-assisted triage of patient input, **live video visits from the patient's chart**, prescribing (per-tenant opt-in, ADR 010), safety alerts at the point of prescribing | member of one or more organizations |
| **Clinic / practice** | SMB organization (the revision-1 tenant) | its own clinicians, patients and clinical records, self-service member onboarding | **practice tier tenant** (one database per tenant, ADR 002) |
| **Hospital / multi-site** | enterprise organization | the same plus locations, departments, SSO, extended audit, a stricter residency posture and — if its compliance team requires it — a **dedicated media configuration** (ADR 009) | **enterprise tier tenant** (dedicated isolation; U21) |
| **Platform operator** | Mendarion | tenant lifecycle, the public directory index and knowledge services, PHI-free aggregation | platform store (PHI-free by design) |
| **Pharmacy** *(staged)* | licensed partner (or our own entity — U25) | dispensing, refill data, e-prescribing network (V3 tier) | integration boundary, not a tenant |

### Identity, tenancy and sharing model (revision 2)

1. **Practice-as-tenant stays** — practices and hospitals are tenants with their own clinical stores (ADR 002 **amended** for the two tiers; ADR 006 **superseded**: patients now hold real accounts, not magic links).
2. **The patient owns the master record** — demographics, conditions, medications, documents — and **grants read access** to it. Practices keep **their own parts** (encounter notes, prescriptions, orders) in their tenant store and share those through **scoped grants** as well.
3. **No snapshot copies.** Sharing is a grant (explicit, scoped, time-boxed, auditable, immediately revocable) resolved at read time, so revocation is real. The **grant/consent service is the only path** between stores.
4. **The directory is PHI-free and public** — practitioner/clinic profiles, specialties, availability hints; searchable **before** an account exists (Compass §4.7). Never clinical data; the platform store holds the index (A28).
5. **Warnings and clinical output stay clinically gated** — the clinician sees safety warnings first; the patient-facing copy follows an acknowledgement. *(Concept divergence, recorded: concept rev 2 §5/§9 describe Sentinel warning "both sides" in parallel; the owner ruled **clinician-first** on 2026-09-24, so the patient-facing copy is staged until U15 signs the wording — R26, U26.)*
6. **Prescribing is a real write path, opt-in per tenant** — Mendarion may hold and finalise prescriptions (ADR 010); a tenant that does not opt in keeps the read-only D3 posture. The e-prescribing **network** stays V3. Sentinel is advisory at that point: acknowledge, override with a documented reason, or accept — **never a silent block**.

### Capability map (revision 2, staged)

| # | Capability | Demo milestone (2 weeks, synthetic) | Staged after |
|---|-----------|--------------------------------------|--------------|
| 1 | Consumer signup + account | **yes** (mock verification, U27) | real identity assurance |
| 2 | Practitioner/clinic directory + browse | **yes** (seeded profiles) | search, availability, ratings |
| 3 | Patient master file | **yes** (basic fields) | imports, documents, device data |
| 4 | Share a file with a doctor (grant) | **yes** (one grant, read-only) | multi-grant, scopes, expiry UX, revocation audit |
| 5 | Practice loop — check-in → Cockpit-lite → AI feedback triage | **yes** (revision-1 spine, unchanged) | as specified in `check-in-feedback` / `assist-ai` |
| 6 | AI symptom → physician routing | no (UI stub only) | **1st after the demo** (owner 2026-09-24): mandatory-confirmation rule, red-flag path, evaluation set (U23/R24) |
| 7 | Practice self-service + member assignment | no | 2nd: invitations, roles, subscription (U12) |
| 8 | Virtual meetings with patients — **live clinician↔patient consultation** (shape decided 2026-09-24, U24) | no | 3rd: build-vs-buy + consent/recording (U24, U13). The concept's async staff-triaged short-video check-in is a **separate** pattern, not planned |
| 9 | Virtual pharmacy | no | 4th: partner/licence first (U25, R25) |
| 10 | Instant medication + occupation warnings (**Sentinel**) | no | **1st after the demo, with item 6** (owner 2026-09-24): deterministic cited rules from a **licensed clinical drug-data source** (U30), clinician-first (U26, R26); concept's patient-facing copy staged until U15 |
| 11 | Hospital / enterprise tier onboarding | no | not sequenced by the 2026-09-24 ordering decision: dedicated isolation, SSO, extended audit, **dedicated media configuration** (U21, U13, ADR 009) |
| 12 | Prescribing in-product — write path + Sentinel gate (network transmission = V3) | no | sequenced **with items 6 + 10** *(assumed — Sentinel's alert is at the point of prescribing, so the write path is what makes it real)*: per-tenant opt-in, override logged, never a silent block (ADR 010, R32, U13/U30) |
| 13 | Compass specifics beyond the demo's directory: filters (specialty/condition/location/language/**insurance**/**next available slot**), per-professional visibility + capacity controls, **verified aggregate reviews** | no | V2 tier per concept §12; requires availability/scheduling and insurance data domains (U11 reopen, U31) |

### What revision 1 keeps (no re-litigation)

The practice-side slice and its SPECs (`check-in-feedback` **Approved**, `assist-ai` **Approved** 2026-09-26 with the U15 carve-out on the claims wording — all seven SPEC files are Approved as of 2026-09-26), the standards in `.work/standards/`, ADR 001 (FastAPI; interpreter amended by **019**), 003 (Redis), 004 (hosting/region, U13), 005 (AI egress/redaction), 007 (AI advisory posture — extended by the routing ADR), and the Docker `dev`/`prd` stack (ADR 008) all remain in force.

### What revision 1 said that revision 2 supersedes

| Revision 1 | Revision 2 |
|------------|------------|
| Patient access = signed magic links, **no patient account system** (ADR 006) | public patient accounts + global identity; ADR 006 **superseded** |
| One tenant, one practice (doc 04 §2) | practice tier + enterprise/hospital tier (U21) |
| PHI stays inside the practice's tenant store | patient-owned master record + bilateral grants between stores (U22) |
| Pharmacy = integration only at V3; no telehealth | pharmacy and virtual meetings are **staged product capabilities**, licence/partnership-gated (U24/U25); telehealth delivery decided in **ADR 009** (managed vendor behind an adapter), Live named as a pillar (concept rev 2 §4.8) |
| "No AI output reaches the patient" (ADR 007 rule 1) | patient-facing **routing suggestions** allowed, with staff confirmation where required (U23) — ADR 007 extended, wording via U15. Sentinel's patient-facing copy is **staged** (clinician-first retained, U26) |
| Every clinical path is **read-only toward the practice's system**; "no write-back ever" (D3, doc 04 BC6) | **prescribing is a real write path**, opt-in per tenant (ADR 010); the read-only *import* posture for clinical data is unchanged and non-opted-in tenants keep the D3 posture; e-prescribing **network** transmission stays V3 |
| Six pillars; no consumer discovery, no visits, no safety layer | concept rev 2 = **Eight pillars** + Sentinel: **Compass** (public discovery, AI matching, enrollment), **Live** (telehealth visits), **Sentinel** (AI medication-safety layer); absorbed above |

### Success criteria (revision 2 additions — owner-accepted 2026-09-24)

S1–S3 above stay the practice-side pilot targets. The revision adds three criteria for the consumer/provider product; they were proposed as **assumed** and **accepted by the owner** on 2026-09-24 (they also become the seeds of the U15 evaluation harness):

| # | Criterion | Measure |
|---|-----------|---------|
| S4 | Consumer onboarding works unaided | In the synthetic demo, a person completes signup → directory → file → grant → the clinician views the shared file **in ≤10 min without help** |
| S5 | Routing is right and never silent about danger | ≥90% correct specialty on a labelled set, with **zero missed red-flags** (a red-flag presentation routes to emergency care regardless of AI or confirmation) |
| S6 | Safety warnings do not miss high-severity cases | **Zero missed** high-severity rule hits on the labelled set (occupation × sedating-medication class), each with a cited source |

Basis: owner answer 2026-09-24 ("Accept the proposed consumer/provider criteria"). S5/S6 are **pilot/pilot-readiness** measures — the demo only needs the seeded rules and the labelled set to exist.

### NFR additions for the revision-2 surfaces (owner-accepted 2026-09-24)

Proposed as **assumed** (derived from the accepted practice-side set) and accepted by the owner; doc 04 §5 carries the operative table once P1 runs.

| Area | Target |
|------|--------|
| Live consultation (video) | 720p target; audio survives degradation — drop video below ~1 Mbps; one-way latency < 300 ms |
| Live resilience (concept §6) | **automatic audio-only fallback** and a **dial-in / phone fallback** for patients without usable data; an automated **device/connection check** before the waiting room |
| Live isolation | an enterprise tenant may be routed to a **dedicated media configuration** (ADR 009); recordings never leave the tenant store |
| Availability — enterprise/hospital tier | 99.9% monthly (practice tier stays 99.5%) |
| Directory search | p95 < 300 ms (**public, unauthenticated** — Compass §4.7) |
| Grant revocation propagation | effective ≤ 5 s after revocation (no snapshot copies to invalidate — U22) |
| Consumer signup | p95 < 2 s |
| Recording consent | recording **off by default**, enabled per tenant/session with recorded consent; transcripts/scans are V3 (concept §12) |

### Demo acceptance (revision 2, synthetic data only)

- [ ] A new person can sign up, find a seeded practitioner in the directory, and open their profile.
- [ ] The same person can create a basic file and share it with that practitioner through a grant.
- [ ] The practitioner can open the shared file and see exactly what the grant allows.
- [ ] The revision-1 loop still works end-to-end on the same instance (check-in → cockpit-lite → AI triage).
- [ ] A revoked grant stops access immediately.
- [ ] No real patient data anywhere; no live AI vendor needed (any model call is stubbed or sandboxed).

### Open in revision 2 — **all foundation items closed 2026-09-25**

**Closed:** U21/U22/U23/U26/U28 (P0 grill, 2026-09-24) · U24 (telehealth shape + mechanism → ADR 009) · U25 (**partner-only, never dispense**) · U27 (identity assurance → **ADR 012**) · U31 (recording: opt-in, 7-year retention, tenant object storage → ADR 015) · **U34 (patient plane → dedicated consumer store, ADR 011)**. **Carried with owners (none blocks the demo):** U6 (which side the first post-demo milestone optimises) · U12 (business model) · U13 (jurisdiction + residency) · U14 (AI vendor agreement + redaction evidence) · U15 (patient-facing AI wording + S5/S6 pass bars — internal CTO collaborator) · U29/U30/U32/U33 (telehealth vendor, licensed drug-data source, Compass data deps, object-storage service — each Deferred against a **staged** milestone).

**Status:** the probe re-ran (iteration 9, coverage **90%**, target met), P0–P3 and P6 are re-passed for revision 2, and **plan-master-ready: yes (2026-09-25)** — the master implementation plan is authored next (`.work/plans/full/20260925-full-plan.md`, **Proposed**).

## Audience and document purpose

| Layer | Audience | What they need |
|-------|----------|----------------|
| **Development** | Engineers and agent sessions | v1 boundaries, tenant/PHI invariants, capability map, explicit unknowns |
| **Shipped product** | Clinicians and patients | UX, help, onboarding — **out of scope here**; persona/journey detail feeds `.work.ui/` |

This is the **P0 mini-plan**: product intent, scope, capabilities, open decisions. It is **not** the architecture foundation (doc 04) and **not** the master plan (`*-full-plan.md`, owned by `@plan-master`).

---

## Assumption ledger

### Founder intent (verbatim - P0 capture)

Operator directive (2026-09-24, `@plan-foundation greenfield`, verbatim):

> "@plan-foundation greenfield - based on: ".work/prompts/Meridian — Practice Intelligence & Patient Connection OS.html"  - we need a solid awesome innovative product that's easy to use for both the medicine professional and the patient."

Source concept, quoted verbatim (only the market-research and Sources sections are omitted; read the file for the full text):

> **One-liner:** Mendarion is the operating system for modern clinical practice — it gives physicians the stats, graphs, and prescription intelligence they've never had, gives patients a real sense of closeness to the person treating them, and gives clinics and hospitals a single, secure, multi-tenant home for both.
>
> **Executive Summary** — Every existing category touches one piece of this problem: EHRs own the chart, patient portals own the messaging, medication-adherence apps (Medisafe, MyTherapy, Care4Today) own the pill reminder, and practice-management tools own the billing. None of them own the relationship — the thing that actually makes medicine work. Mendarion is built around a simple bet: if you give physicians better visibility into their own practice, and give patients a genuine feeling of being seen between visits, outcomes and retention both improve, and the software pays for itself. Mendarion is a multi-tenant SaaS platform. Each clinic, hospital department, or solo practice is a tenant with its own isolated clinical data store; a centralized layer handles platform ownership, billing, cross-tenant benchmarking (opt-in, de-identified), and system administration.
>
> **Vision** — Mendarion should feel like two products fused into one, because it is solving two problems at once: For the professional — a personal analytics cockpit. Every physician gets the equivalent of a Strava for their practice: their outcomes, their prescribing patterns, their patient trends, benchmarked against their own history and (opt-in) their peers. For the patient — a companion that makes the relationship feel continuous instead of transactional: a visible care timeline, lightweight check-ins, and two-way visibility into how a treatment is actually going. Both feed the same underlying data model, so the "closeness" the patient feels is literally the same signal that produces the physician's stats — engagement and outcome data flow in one loop instead of two disconnected apps.
>
> **Why now (data points, as cited by the concept)** — 96% of physicians say time spent on data input/reporting increased over the last decade; ~80% report being personally at risk of burnout; 86% say reporting demands diminished their joy in practicing medicine. Patient-engagement software market placed at $27–47B (2025–2026), 12–18% CAGR.

### Operator answers, round 2 (verbatim - 2026-09-24)

> "1. Team: 1 developer"
>
> "2. the system/app is useful to the medical professional, he can keep track of patients, prescribed medication, stats on his practice, and the patient is able to provide feedback.
> It is important, this app/system must provide the option to use AI to filter/process feedback from patients, as well as research medications, and match symptoms to medications, for the professional's consideration only."

Follow-up answers in the same session: success criteria → **"all the above"** (all three metric sets accepted — see §Success criteria v1); AI data path → **"Third-party API, but only after de-identification/redaction in our layer"**.

### Confirmed facts (repository evidence)

- `.cursorrules` exists at repo root; project name is **Mendarion** (set 2026-09-24, repo slug `mendarion`), thin-client Agent OS with `AGENT_OS_SOURCE=/mnt/work/Projects/pilo.ai.logicbison` (`.cursorrules:L65`).
- `.work/` planning tree present: `plans/{NEXT.md,ASSUMPTIONS.md,RISK_REGISTRY.md,UNKNOWNS.md}`, `context/HANDOFF.md`, `.work.ui/`.
- Proprietary license in place: `LICENSE`, holder `3-102-970973 LIMITADA`; `LICENSE` is a protected surface (`.work/PROTECTED_SURFACES.json`).
- Distribution target is private: `gh api repos/PiloTracer/mendarion` → `private: true`, default branch `main`, baseline commit `1a69db8`.
- Source concept doc present and committed: `.work/prompts/Meridian — Practice Intelligence & Patient Connection OS.html` (23,726 B; sections 1–11).
- No product code and **no CI** yet (UNKNOWNS U2 open). The stack *is* pinned in `DOCS_TECH_STACK.md` (U1 closed, P4) and propagated into `.cursorrules` (U20 closed); the six binding standards are on disk (U3 closed, P3/P4); the protected compose/dev-stack files exist (P5, owner-approved 2026-09-24).

### Inferences (plausible, not proven)

- **I1 — Brand vs project name. RESOLVED (D1, 2026-09-24).** Operator: "Use Mendarion as the project name too (docs, README, .cursorrules)". Documents, README and `.cursorrules` now say **Mendarion**; the repo directory and GitHub remote keep the `mendarion` slug.
- **I2 — Launch geography. RESOLVED (D2) — the original inference was rejected.** The Costa-Rican holder suggested LATAM-first, but the operator chose **global, languages EN + ES**. Consequence: multi-regime compliance (HIPAA + GDPR + LATAM health law) and data-residency decisions now sit in v1 (UNKNOWNS U13); A4 (LATAM-first) is rejected.
- **I3 — Build-alongside posture. RESOLVED (D3, 2026-09-24) · AMENDED 2026-09-24 (ADR 010).** Operator: "Beside the EHR, with one read-only import path in v1 (FHIR/HL7 where available, CSV otherwise)". Read-only import therefore moves from the concept's V2 into v1. **Amendment:** the owner's concept revision 2 + answer ("Prescribe in-product now, network transmission at V3") opens the **prescribing write path** — Mendarion may hold/finalise prescriptions, **opt-in per tenant** (ADR 010); tenants that do not opt in keep the pure read-only posture. The **read-only import** posture for clinical data is unchanged, and e-prescribing **network** transmission stays V3. Consequence: doc 04 BC6's "no write-back ever" must be amended in P1, and the divergence is logged as **R32**.
- **I4 — Dual-surface scope.** "Two products fused into one" means v1 needs **two** first-class surfaces (clinician web cockpit + patient mobile companion) plus an org/admin surface — three UX contexts, one data model. Cost implication for the MVP timeline is unresolved (*Open question 1*).
- **I5 — Regulated-development constraint.** Because the domain is PHI, all development and agent work must run on synthetic patients; this is inferred from `.cursorrules` §Data Privacy & Security + §Test data, not yet stated by the owner for this product.

### Unknowns (decide with stakeholders)

| # | Unknown | Impact |
|---|---------|--------|
| U6 | Which side is optimized first in v1 (clinician cockpit vs patient companion) | UX priority, which pillar is MVP-critical, demo narrative |
| U7 | ~~v1 clinical-data intake path~~ **Closed 2026-09-24** — beside the EHR, one read-only import path (FHIR/HL7 where available, CSV otherwise) | Integration scope and data model fixed for v1 |
| U8 | ~~Launch market and jurisdiction~~ **Closed 2026-09-24** — global, languages EN + ES | Residency/jurisdiction specifics carried by U13 |
| U9 | Team size, skills, budget ceiling, MVP deadline | Scope cuts, stack, hosting tier, plan-master milestones |
| U10 | Measurable v1 success criteria | P1 NFR targets, milestone acceptance, traceability (S4-7) |
| U11 | Is scheduling/intake in v1? (Staff workspace implies it; the MVP line omits it) | Bounded contexts, integrations, Org module depth |
| U12 | Confirmation of the business model (per-provider seat pricing + benchmarking revenue) | Multi-tenant billing/subscription design in the platform layer |
| U13 | Primary regulatory jurisdiction and data-residency placement for a global launch (HIPAA vs GDPR vs LATAM health law; single region or per-region storage) | Hosting + key management, DPA/BAA set, retention and erasure workflows |

These rows are mirrored in `.work/plans/UNKNOWNS.md` (U6–U12, same ids).

---

## Product scope (v1)

> **Revision 1 section — superseded where it conflicts with §Revision 2 above** (which is the current scope). Kept as the record of the accepted practice-side slice.

### In scope (from the concept's MVP line, verbatim)

> MVP: Core tenant provisioning, Cockpit (basic stats), Rx Radar (personal prescribing history), The Loop (adherence logging + alerts), Closer (messaging + Health Timeline v1), basic Org (roles + single-location org chart)

Plus, by operator decision D3 (2026-09-24): a **single read-only clinical-data import path** (FHIR/HL7 where the practice's EHR exposes it, CSV otherwise), so chart data reaches Cockpit and Rx Radar without re-entry. EN + ES localization is a v1 requirement (D2).

Plus, by operator requirement (2026-09-24): an **AI assist layer** with three v1 jobs — patient-feedback triage/summarization, medication research, and symptom→medication matching — advisory only, with patient feedback redacted in our layer before any third-party call. The operator's words: "must provide the option to use AI to filter/process feedback from patients, as well as research medications, and match symptoms to medications, **for the professional's consideration only**".

### Out of scope (v1)

Deferred by the concept's own roadmap:

- Peer benchmarking / opt-in de-identified aggregate layer (concept V2)
- Medication Digital Twin (V2)
- Care Circle / caregiver visibility (V2)
- Multi-location Org + location rollup reporting (V2)
- FHIR-based EHR **write-back/export** and deep bidirectional interop (the concept's V2 line about *read-only* import is superseded by decision D3)
- Languages beyond EN + ES (D2)
- Autonomous or patient-facing AI: no auto-prescribing, auto-diagnosis, automated patient messaging, or AI advice reaching the patient without clinician review (AI output is "for the professional's consideration only")
- E-prescribing network integration (e.g. Surescripts-class) (V3)
- Pharmacy refill/adherence data integration (V3)
- Enterprise dedicated-database tier, SSO, SOC 2 Type II (V3)
- Configurable Cockpit dashboard/widget builder (V3)

Never mentioned in the concept; treated as out of scope unless the owner says otherwise (*Open question 3*):

- Claims/billing/RCM processing for the practice (the concept explicitly leaves billing to practice-management tools; Mendarion's billing is its own multi-tenant subscription)
- Full EHR/chart replacement (see I3 — needs *Decision 3* to hold)
- Imaging/PACS, lab ordering, e-commerce, POS, inventory

---

## Personas (D2 — concept §3, stated)

> **Revision 1 section — the revision-2 segment set (§Revision 2 §Who it is for) adds the consumer as a principal, the enterprise/hospital organization and the pharmacy partner.** The P1–P7 rows below still describe the practice-side product.

| # | Persona | Core need | Primary surface | v1 |
|---|---------|-----------|-----------------|----|
| P1 | Platform Owner (Mendarion, the company) | Provision tenants, billing/licensing, system health, benchmarking data business | Owner Console (web) | partial — provisioning + basic billing state |
| P2 | Institution Admin | Staff, departments, locations, roles, credentials, org billing | Admin Console (web) | partial — roles + single-location org chart |
| P3 | Physician / Therapist / Clinician | Own practice stats, prescription/outcome tracking, efficient patient communication | Clinician Cockpit (web + mobile) | **yes** — primary persona |
| P4 | Clinical / Front-desk Staff | Scheduling, intake, task routing, limited record access per role | Staff workspace (web) | partial — roles only (see U11) |
| P5 | Patient | Understand the care plan, log how they are doing, feel connected | Patient Companion (mobile-first) | **yes** — primary persona |
| P6 | Caregiver / family member (patient-granted) | Support a loved one with limited visibility | Care Circle (mobile) | no — V2 |
| P7 | (implied) Support agent at the platform owner | Time-boxed, audited access to a tenant | Owner Console | no — V2/V3, but the audit invariant is in v1 |

---

## Functional capabilities (D4 — concept §4, stated)

> **Revision 1 section — the revision-2 capability map (with demo/staged labels) is §Revision 2 §Capability map.** Six pillars below remain the practice-side product; the consumer, routing, telehealth, pharmacy and safety-alert capabilities are new in revision 2.

| Pillar | Core capability | v1 slice | Concept § |
|--------|-----------------|----------|-----------|
| **Cockpit** | Physician practice intelligence: panel trends, visit duration, no-shows, diagnosis mix, outcome trends, composite **Practice Pulse**, peer benchmarking, quality-program exports | basic stats + Practice Pulse; **no** benchmarking (V2) | 4.1 |
| **Rx Radar** | Longitudinal personal prescribing analytics, Medication Digital Twin, interaction/duplicate-therapy flags, refill+adherence linkage, formulary/cost awareness, institution-wide prescribing variance | personal prescribing history; Digital Twin and formulary/cost are V2+ | 4.2 |
| **The Loop** | Medication results and adherence: lightweight patient logging (adherence taps, side-effect/symptom, mood/pain/function), synthesized correlation for the clinician, threshold alerts, shared editable care plan | adherence logging + alerts (predictive-leaning, not reactive-only) | 4.3 |
| **Closer** | Patient connection: Health Timeline, secure async messaging + short video check-ins with staff triage, between-visit micro check-ins, Care Circle, auto visit-prep/recap | messaging + Health Timeline v1; Care Circle is V2 | 4.4 |
| **Org** | Institution/team management: visual organigram, role-based access to data-category granularity, credential/license expiry tracking, multi-location rollups, self-service onboarding | roles + single-location org chart | 4.5 |
| **Command** | Platform owner console: tenant provisioning/lifecycle, cross-tenant usage/health/billing analytics (never clinical data), feature flags/staged rollout, audited support impersonation, benchmarking dataset administration | provisioning + lifecycle + audited support access | 4.6 |
| **Assist (AI)** — *v1 must-have (operator 2026-09-24)* | Clinician-facing assistance on three jobs: **filter/process patient feedback**, **medication research**, **symptom→medication matching**. Advisory only: results are presented for the professional's consideration with provenance, never applied automatically | v1: all three jobs; input redacted before leaving our boundary; output clinician-reviewed; prompt design MOD-07, cost estimate MOD-03 | operator |

Shared **visual grammar** (concept "Visual Language, Consolidated"): Health Timeline, Medication Digital Twin, Practice Pulse, Organigram, dashboard/widget builder. Reusing one visual primitive set is what makes the six pillars feel like one product — a UX constraint the `.work.ui/` foundation must honor (feeds S4-9).


**AI assist layer — binding design rules for v1:** (1) advisory only — the clinician reviews and decides, nothing is auto-applied; (2) patient feedback is de-identified/redacted **in our layer** before any third-party model call, and that redaction is treated as risk reduction, not as legal de-identification (GDPR: pseudonymised data is still personal data); (3) every AI output carries provenance (which input produced it) and is auditable; (4) no AI output reaches the patient directly. Concept ids to run when this layer is specified: **MOD-07** (prompt composition, SPEC §15) and **MOD-03** (billable-unit cost estimate in the AI ADR).

---

## Success criteria (v1)

> **Revision 1 section — the revision-2 demo acceptance list (the first milestone) is §Revision 2 §Demo acceptance.** S1–S3 stay the product-level criteria.

Operator answer 2026-09-24 — asked which measurable targets the MVP is scored against: **"all the above"** (all three sets are binding).

| # | Criterion | Measure |
|---|-----------|---------|
| S1 | Pilot engagement — the cockpit is actually used | ≥70% of pilot clinicians use the Cockpit weekly; ≥80% of incoming patient feedback triaged within 24 h; ≥50% of invited patients log ≥1 check-in per month |
| S2 | Clinical movement — the loop changes behaviour | Medication adherence +10 percentage points over the practice's own baseline within 90 days; follow-up completion +15%; no-show rate −10% |
| S3 | AI usefulness — assistance earns its keep | A clinician saves or acts on an AI suggestion in ≥30% of the cases where it is shown; <2 min of clinician time per patient per week reviewing incoming feedback |

These are the MVP acceptance targets the master plan must trace to (S4-7) and the numbers `p1-nfr` must be sized against.

**Deadline caveat (2026-09-24, confirmed):** the deliverable is an internal demo on synthetic data, so S1–S3 cannot be *measured* at delivery — S2 needs a 90-day window and S1/S3 need real users. They are **pilot-phase targets**; the demo is judged on doc 04 §2's slice working end-to-end. Owner-confirmed: deliverable type D6, slice D7, NFRs D8.

---

## Non-functional expectations

Quantified targets were accepted at P1 (owner 2026-09-24) and live in the architecture foundation — `.work/plans/foundation/20260924-04-foundation-architecture.md` §5 (cockpit p95 1.5 s · check-in p95 1 s · AI suggestion p95 30 s · 99.5% availability · RPO 24 h / RTO 4 h · K–M rows · WCAG 2.2 AA · AI spend ≤ 5% of seat revenue); U10 closed. Already binding as **invariants** (stated in the concept §5–§6, not negotiable without an ADR):

| Area | Invariant | Concept § |
|------|-----------|-----------|
| Tenancy isolation | Tenant scoping enforced **at the data-access/query layer**, not only in the UI; RLS is defense-in-depth, never the sole mechanism | 5 |
| PHI boundary | Raw PHI never crosses a tenant boundary; the shared platform layer stores platform-operational data only; only de-identified, aggregated, opt-in statistics are copied out | 5 |
| Audit | Every access to PHI is logged, including time-boxed platform-owner support impersonation | 6 |
| Consent | Explicit, granular, revocable consent for every data-sharing feature (Care Circle, benchmarking, research) | 6 |
| Compliance posture | HIPAA-compliant hosting + BAA per tenant; GDPR-aware for international tenants; SOC 2 Type II as a milestone (V3) | 6 |
| Locales / i18n | **EN** in the 2-week slice, with all copy in locale files; **ES is the next slice** — an owner-accepted amendment of D2 (2026-09-24), recorded as R17 | D2 amended |
| AI data path | Patient feedback is de-identified/redacted **in our layer** before any third-party model call (operator 2026-09-24); vendor agreements still required because redaction is not legal de-identification | operator |
| AI is advisory | AI output reaches the clinician for consideration only — with provenance and a review affordance; the system never auto-prescribes, auto-diagnoses or messages a patient from AI output | operator |

---

## Data model (provisional — full table in doc 04 §6)

| Entity | Relationship | Volume class (pilot) | Sensitivity |
|--------|--------------|----------------------|-------------|
| `tenant` | 1—N all clinical rows (slice: 1) | 1–10 | internal config |
| `staff_user` | N—1 tenant | 10–100 | **PII**: name, email, phone, licence number |
| `patient` | N—1 tenant; 1—N children | 1k–10k | **PHI**: name, DOB, contact, MRN, address |
| `encounter` / `medication` | N—1 patient | 10k–100k each | **PHI**: dates, notes; drug, dose, start/stop |
| `checkin` | N—1 patient | 100k–500k/yr | **PHI**: adherence, symptom/pain/mood scores |
| `feedback_item` → `redacted_text` | N—1 check-in; 1—1 redaction twin | same | **PHI**: free text — highest-risk field in the product |
| `ai_suggestion` | N—1 check-in; N—1 model run | 1 per triaged item | derived from redacted text; model id, prompt hash, output, provenance, accept/reject |
| `signal_rule` / `attention_flag` | N—1 tenant / patient | tens / thousands | internal, clinically meaningful → treat as PHI |
| `consent` | N—1 patient | per patient | **PII/PHI**: type, timestamp, revocation |
| `audit_event` | append-only | M rows/yr | no clinical content (actor, resource id, action, time) |

Retention/erasure/residency are blocked on U13. The `p1-data-model` grill was **accepted 2026-09-24** (U17 closed) and exercised at `p2-database` (ADR 002); doc 04 §6 is the operative table.

---

## Constraints (D8)

Operator answers 2026-09-24, verbatim: **"Team: 1 developer"** · **"2 weeks for this mvp"** (≈10 working days).

- **Binding:** one developer builds tenant provisioning, Cockpit, Rx Radar, The Loop, Closer, Org basics, the AI assist layer and the read-only import path — in two weeks.
- **Consequence, stated plainly:** the P0 MVP line cannot be built in 10 working days (R8/R13/**R16**). The recommended cut is one loop-shaped vertical slice — patient check-in → clinician cockpit-lite → AI feedback triage — with CSV seeding instead of FHIR (doc 04 §2) — accepted by the owner 2026-09-24 (U17 closed).
- **Operational consequence:** a solo maintainer cannot operate a multi-service platform, so P2/P5 choices must favour the fewest moving parts and managed services — decided with evidence at that point, not by silent default.
- **Deliverable (P1, 2026-09-24):** an **internal demo on synthetic data** — so production PHI, vendor BAA/DPA, consent capture and production auth are **out of the slice**; the tenancy + audit schema still gets built because it costs nothing extra now and avoids a rewrite at pilot time.
- **Closed 2026-09-24:** budget ceiling is not a tracked constraint and ops are owner-managed (U9); sizing recommendations stay lean but are no longer budget-blocked (Recommendation protocol rule 6).

---

## Architecture directions (non-prescriptive - architecture foundation in doc 04)

Recorded as **directions** from the concept (§5, §8); ADRs are chosen in P2, bounded contexts and dependency direction land in doc 04.

- **Hybrid tenancy:** schema-isolated pool for SMB tenants, database-per-tenant (dedicated keys/infrastructure where required) for enterprise; tenant tier is a mutable attribute upgradeable without a customer-visible migration.
- **Two data planes:** tenant clinical stores (PHI) vs a centralized platform layer (tenant registry, billing/subscription state, support tickets, product telemetry, feature flags, org metadata) that is PHI-free by design.
- **Store shape:** PostgreSQL per tenant with row-level security as defense-in-depth; separate platform PostgreSQL cluster; asynchronous OLAP/aggregation layer for reporting so heavy analytics never touch transactional clinical systems.
- **Service shape:** service-oriented backend with a tenancy-aware data-access layer abstracting schema-per-tenant vs database-per-tenant routing, plus an event bus for cross-service sync (e.g. a logged symptom triggering a clinician alert).
- **Surfaces:** web app for clinicians/admins, mobile-first app for patients, both on one API layer.
- **Interoperability (post-MVP):** HL7 FHIR for import/export and EHR interop; e-prescribing network connectivity; pharmacy APIs for refill/adherence.

---

## How `.cursorrules` applies

No overrides requested; Core Principles 1–7 are not forkable. Project-specific consequences:

| `.cursorrules` rule | Consequence for Mendarion |
|---------------------|---------------------------|
| §Data Privacy & Security — no PII in logs, sanitize errors | PHI-safe logging is a **product** requirement too (concept §6 audit invariant): log ids/status only |
| §Test data — synthetic/mock only | All development, fixtures and demos run on **synthetic patients**; never tenant PHI in the repo, in prompts, or in agent sessions |
| §Protective files | `LICENSE` (proprietary grant), `.cursorrules`, stack/compose files need same-message owner approval |
| §Database & Schema Rules | Numbered idempotent migrations per tenant store; destructive ops need same-message approval |
| §Docker / Dev Environment | Once the stack lands (P5), every test/lint/type runs inside the documented compose service |
| MOD-06 (AI-assisted code) | Applies from the first line of implementation; foundation artifacts are agent-authored (`AI-assisted: yes`) |
| §Workflow — scope first | Every implementation iteration declares `Files` in `NEXT.md` / `.work/touch-scope` before writing |

---

## Risks (top; registry: `.work/plans/RISK_REGISTRY.md`)

| Id | Risk | Why it matters here |
|----|------|---------------------|
| R4 | Cross-tenant PHI leakage | Reportable breach under HIPAA; the concept's whole isolation design exists to prevent it |
| R5 | Physician adoption fatigue | "Another new tool" — only survivable with zero-extra-data-entry and an immediately useful cockpit (see I3/U7) |
| R6 | Patient engagement drop-off | Adherence apps have mixed real-world stickiness; patient-side actions must stay seconds-long and visibly tied to the Health Timeline |
| R7 | Regulatory/interoperability complexity | FHIR/e-prescribing/pharmacy integration is deep work; sequence after strong standalone value |
| R8 | Two-surface MVP overreach | Cockpit + companion + org/admin in one MVP with unknown team size (I4, U9) |
| R9 | PHI exposure through AI-assisted development | Prompts/tools/CI can leak real patient data; mitigated by synthetic-data-only rule |
| R11 | AI output mistaken for clinical advice (CDS / medical-device boundary) | Symptom→medication matching sits close to regulated clinical decision support; "for consideration only" framing, disclaimers and human review are the defence, and the wording is market-specific (U13/U15) |
| R12 | Residual PHI reaches a third-party model despite redaction | Free-text feedback is hard to redact perfectly; residual identifiers, re-identification paths and GDPR pseudonymisation rules mean vendor agreements (BAA/DPA) remain necessary (U14) |
| R13 | One-developer capacity vs three surfaces + AI layer | The MVP must fit a solo maintainer: managed services, few moving parts and boring technology become requirements rather than preferences |
| R14 | AI quality/hallucination erodes clinician trust | Medication research and symptom matching can be confidently wrong; needs an evaluation harness, provenance and a fast reject path |
| R15 | Variable AI cost against per-seat pricing | Model spend scales with patient-feedback volume while revenue scales with provider seats; meter AI usage per tenant (MOD-03) and set a fair-use allowance per tier (U12) |

---

## Traceability

| Artifact | Path |
|----------|------|
| Source concept (owner input) | `.work/prompts/Meridian — Practice Intelligence & Patient Connection OS.html` |
| Probe ledger (cover D1–D10) | `.work/plans/foundation/PROBE_LEDGER.md` |
| Registries | `.work/plans/ASSUMPTIONS.md`, `.work/plans/RISK_REGISTRY.md`, `.work/plans/UNKNOWNS.md` |
| Integration resources (doc 02) | `.work/plans/foundation/20260924-02-integration-resources.md` |
| Foundation architecture (doc 04) | `.work/plans/foundation/20260924-04-foundation-architecture.md` |
| Product adjacency (doc 03) | **skipped deliberately** — the 2-week slice has no adjacent module to phase in; revisit after the slice ships |
| Session state | `.work/context/HANDOFF.md`, `.work/plans/NEXT.md` |
| UI foundation (separate framework) | `.work.ui/` + `DOCS_UI_STACK.md` (UI Design OS: `@ui-bootstrap` / `@ui-design-foundation`) |

---

## Decisions needed

Answered by the operator on 2026-09-24 (answers verbatim):

| # | Decision | Answer (verbatim) | Effect |
|---|----------|-------------------|--------|
| 1 | Project/brand naming | "Use Mendarion as the project name too (docs, README, .cursorrules)" | Project name **Mendarion** in docs, README and `.cursorrules`; repo + GitHub slug stay `mendarion`; I1 resolved |
| 2 | Launch market and jurisdiction | "The application is Global, languages: EN + ES" | Multi-regime compliance + residency enter v1 (U13); EN/ES i18n is a v1 requirement; A4 rejected |
| 3 | v1 clinical-data intake model | "Beside the EHR, with one read-only import path in v1 (FHIR/HL7 where available, CSV otherwise)" | Read-only import in v1, write-back deferred; I3 and U7 resolved |
| 4 | MVP deadline and team | "2 weeks for this mvp" (team already answered: 1 developer) | Forces the slice cut in doc 04 §2; S1–S3 become pilot-phase measures (U16/U17) |
| 5 | AI clinical-claims sign-off owner | "cto internal collaborator" | U15 owner = the internal CTO collaborator; route `@cto-director` / `@cto-consult` (`.ai.cto` = `/mnt/work/Projects/pilo.ai.cto.logicbison`) for the decision review |
| 6 | 2-week deliverable type (P1) | "Internal demo / prototype on synthetic data" | No production PHI in the slice ⇒ no vendor BAA/DPA needed yet, demo accounts instead of production auth, hosting choice relaxed; compliance work starts with the pilot (U16 closed) |
| 7 | 2-week delivery slice (P1) | "Accept doc 04 §2 as written" | The loop slice is the demo scope; **D2 amended** — EN only in the slice, ES in the next slice (U17 closed) |
| 8 | NFR defaults (P1) | "Accept the proposed defaults (doc 04 §5)" | The doc 04 §5 numbers become the binding targets for the slice (D5 confirmed) |

None open.

**Round 3 (2026-09-24, concept revision 2 + covering note):** the owner answered the three drifts this revision raised, verbatim: **(1) build order** "Keep today's ordering; treat MVP/V2/V3 as release tiers" · **(2) prescribing** "Prescribe in-product now, network transmission at V3" *(with "optionally" — recorded as **opt-in per tenant**, ADR 010)* · **(3) naming** "The correct name of the product is 'mendarion'… rename everywhere" · plus **(4) Sentinel audience** "Keep clinician-first (U26 as decided 2026-09-24)". Effect: ADR **009** (telehealth delivery) and **010** (prescribing surface) Decided; the product renamed; A31–A34 recorded; U29–U32 opened; R29–R33 added. The concept's own Twilio claim was **corrected** in the record (see ADR 009 References).

**Round 4 (2026-09-24, P1 grills):** **U27** "Contact-verified patients + licence/affiliation-verified professionals" · **U25** "Partner-only: Mendarion never dispenses" · **U31** "Opt-in per session, 7-year clinical retention, tenant object storage". Effect: doc 04 rev 2 §3/§5/§6 updated; U33 (object-storage service) and U34 (patient-plane shape) opened; R25 re-scoped to a design constraint.

### Scope change requested (owner, 2026-09-24) — open

The owner steered the product toward a **direct-to-consumer model**: public signup by any person, doctor/clinic discovery, AI routing of a patient's illness question to a physician from the pool, a patient-held file shared with any doctor, self-service practice signup with member assignment, virtual meetings, a virtual pharmacy, and instant occupational/medication safety warnings. Captured verbatim with an evidence-based impact map and the decisions it forces in **`.work/plans/proposals/20260924-consumer-platform-steer.md`** (§5 = D-S1/D-S2/D-S3).

Recorded honestly: this steer is **not** in the concept doc, and it contradicts ADR 002 (practice-as-tenant), ADR 006 (magic links, no patient accounts), ADR 007 (AI to the professional only) and doc 04 §2 (one tenant; pharmacy at V3). **Until the owner answers, nothing else in this doc or the foundation is amended and `@plan-master greenfield` stays gated.**

## Open questions

1. Who is the named internal CTO collaborator, and does `@cto-bootstrap` / profile-ready have to run before `@cto-consult` can review the AI claims wording and the evaluation gate? (U15 — owner and route recorded.)
2. ~~Budget ceiling and ops model for the pilot?~~ **Closed 2026-09-24** — not a tracked constraint; ops owner-managed (U9).
3. Before the demo becomes a real-patient pilot: AI vendor + contract type and proof the redaction step is sufficient (U14), and jurisdiction + data-residency placement (U13).

Answered at P1 (2026-09-24): deliverable = internal demo on synthetic data; slice = doc 04 §2 as written; NFR defaults = accepted. U11 (scheduling) is out of the slice; revisit for V1.1.

## Next action

`@plan-master greenfield` — author the master implementation plan (`{PLANS_ROOT}/full/YYYYMMDD-full-plan.md`) from this doc, doc 04, the ADRs, the standards, the two feature SPECs and the registries. Foundation P0–P6 is complete and **plan-master-ready** was certified (2026-09-24) — **but that certification is pending re-earning** while the consumer-platform steer above is undecided: the owner first answers `.work/plans/proposals/20260924-consumer-platform-steer.md` §5 (D-S1). `.work/plans/NEXT.md` carries the single next action.
