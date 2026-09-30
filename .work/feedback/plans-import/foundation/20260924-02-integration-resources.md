# Mendarion — integration resources (doc 02)

**Doc:** foundation **02** (integration resources) · **Created:** 2026-09-24 · **Phase:** P1
**Status:** Draft (P1, **status-checked 2026-09-25**) · **Needs:** the deferred vendor selections — **U14** (AI agreement), **U29** (telehealth vendor + BAA), **U30** (licensed drug-data source), **U33** (object-storage service); no vendor artifact is mirrored yet, so this doc lists known integration surfaces without version-pinned mirrors

> Companion documents: doc 01 (`20260924-01-mendarion-initial-scope.md`), doc 04 (`20260924-04-foundation-architecture.md`). Vendor caches belong under `.work/docs/integration/<vendor>-<version>/` with a `MANIFEST.txt` entry.

## 1. Integration inventory (v1 slice)

| # | Integration | Direction | Kind | v1 posture | Evidence |
|---|-------------|-----------|------|-----------|----------|
| I1 | Practice EHR (**FHIR R4**, else HL7 v2) | inbound, read-only | REST / file | **Interface designed, implementation deferred** — the 2-week slice seeds via CSV; FHIR lands in the next slice | operator decision D3 |
| I2 | **CSV import** (patients, medications) | inbound, read-only | file | In the slice; one-off admin action with idempotent re-runs | D3 ("CSV otherwise") |
| I3 | **AI model provider** (LLM) | outbound + inbound | HTTPS API | In the slice, but only *after* in-layer redaction; advisory output only | operator 2026-09-24 |
| I4 | E-prescribing network (Surescripts-class) | outbound | API | Out of scope → V3 | concept §5/§8 |
| I5 | Pharmacy refill/adherence data | inbound | API | Out of scope → V3 | concept §5/§8 |
| I6 | Enterprise SSO / IdP | inbound | OIDC/SAML | Out of scope → V3 (enterprise tier) | concept §9 |
| I7 | **Telehealth video vendor** (managed HIPAA-eligible WebRTC) | outbound (media) + inbound (events) | vendor SDK/REST + WebRTC | **Approach Decided (ADR 009)**; vendor selection → **U29**; BAA + residency are hard gates | concept rev 2 §6 · owner 2026-09-24 |
| I8 | **Licensed clinical drug-interaction data source** (Sentinel's knowledge base) | inbound + outbound (lookups) | API / licensed dataset | Required by Sentinel before it ships — **never a general-purpose model's output** (concept §5); licence + cost → **U30** | concept rev 2 §5 |
| I9 | **Telephony / dial-in provider** (Live's phone fallback) | outbound + inbound | SIP/PSTN via the video vendor where offered, else a voice vendor | Staged with Live; a separate vendor line if the video vendor cannot dial in | concept rev 2 §6 |
| I10 | **Transcription / visit-transcript service** | outbound + inbound | vendor or in-tenant STT | **V3** (concept §12: transcript-aware Sentinel v2); carries the ADR 005 PHI-egress constraint — never sent unredacted to a third party | concept rev 2 §5/§12 · ADR 005 |

## 2. Per-integration notes

### I1 — FHIR read-only import (designed, not built in the slice)

- **Scope when built:** `Patient`, `Encounter`, `MedicationRequest`/`MedicationStatement` (read only); no writes ever; no subscription/webhook push in the first iteration.
- **Auth:** SMART-on-FHIR style OAuth2 where the vendor supports it, otherwise vendor API keys held per tenant in the secret store — never in the repo (`.cursorrules` §Secret scrubbing).
- **Data sensitivity:** highest — pulled objects are PHI and land directly in the tenant store; every pull writes `audit_event` rows.
- **Failure modes:** vendor downtime must never block clinical use (import is asynchronous and resumable); partial pulls are logged and retried, never partially applied without a checkpoint.
- **v1 must-have?** No — the slice's CSV path covers seeding; FHIR is the first post-slice integration because R5 (adoption) depends on chart data arriving without re-entry.

### I2 — CSV import (in the slice)

- Idempotent, dry-run first, per-row error report; no destructive deletes; mapping template checked in under `.work/docs/integration/` when it stabilises.

### I3 — AI model provider (in the slice, contract open)

- **Boundary:** receives **redacted** clinical text only, no identifiers, no patient id (pseudonymous reference); response stored as an `ai_suggestion`, never as clinical record material (doc 04 §7).
- **Contract:** provider must be a contracted processor/sub-processor (BAA/DPA as applicable per U13) — redaction is risk reduction, **not** legal de-identification (R12, U14).
- **Failure modes:** provider outage/rate limit ⇒ silent degrade to "no suggestion"; redaction failure ⇒ **fail closed** (no call).
- **Cost:** billable unit must be modelled (MOD-03) with a per-tenant cap (R15).
- **Open:** vendor, model family, region, retention/training policy of the vendor, and whether a self-hosted fallback is needed for regulated tenants (U14).

### I7 — Telehealth video vendor (approach decided, vendor open)

- **Shape decided (ADR 009 / owner 2026-09-24):** a **managed HIPAA-eligible WebRTC vendor** behind an internal adapter in BC11 — ephemeral rooms per encounter, short-lived single-participant tokens, recordings to **tenant storage** (opt-in), browser join with audio-only + dial-in fallback.
- **Selection criteria for U29 (before any real-patient session):** BAA available and signed; **residency posture compatible with U13** (HIPAA is not GDPR); room/token API and webhook/event surface; recording-to-our-storage support; per-minute pricing for the R15 model; enterprise **dedicated media** option for the enterprise tier.
- **Candidates (from concept rev 2 §6, all to be evidenced at selection — the concept's vendor claims are *claims* until checked):** Daily.co · Vonage Video API · Whereby Embedded · Amazon Chime SDK · LiveKit (later self-host escape hatch). **Not a candidate:** Twilio Programmable Video — closed to new customers (its published EOL page contradicts Twilio's own 2024 reversal).
- **Mirror:** the vendor's API spec/OpenAPI (whichever is selected) gets cached under `.work/docs/integration/<vendor>-<version>/` and logged in `MANIFEST.txt` on selection.

### I8 — Licensed clinical drug-interaction data source (Sentinel's knowledge base)

- **Hard rule (concept §5):** interactions/duplicates/dose ranges/allergy conflicts come from a **licensed clinical drug-data source**, never from a general-purpose model's output. The model is used for narrative phrasing only.
- **Selection criteria for U30:** coverage (interaction severity grading, duplicate therapy, dose ranges by age/renal/hepatic profile), update cadence + versioning (staleness is a safety metric), licensing terms and cost, and whether lookups can run without sending patient identifiers.
- **Mirror:** the licensed dataset's *schema* and a version manifest are cached; bulk data does not live in the repo (licence terms).

### I9 / I10 — Dial-in telephony and transcription

- **I9:** with Live — the video vendor's dial-in where offered, else a voice vendor; a second BAA if a separate vendor is used.
- **I10:** **V3** (transcript-aware Sentinel v2). Transcripts are PHI-derived content and keep ADR 005's fail-closed egress rule; the visit recording and the transcript share the U31 consent/retention policy.

## 3. Mirror policy (why nothing is mirrored yet)

The P1 gate expects a vendor cache + `MANIFEST.txt` when an integration is fixed. Here no vendor is fixed yet (I1 lands post-slice, I3's vendor is U14), so **mirrors are deferred with owners** rather than fabricated:

| Artifact | Status | Owner |
|----------|--------|-------|
| `.work/docs/integration/fhir-r4-<version>/` (CapabilityStatement subset + Patient/Encounter/Medication profiles) | deferred until the first vendor is chosen; use the public FHIR R4 spec until then | P2/P3, with the importing tenant's vendor |
| `.work/docs/integration/<ai-vendor>-<version>/` (API reference, data-retention terms, DPA/BAA) | deferred → U14 | owner + CTO collaborator review |

## 4. Risks and decisions

- R7 (interoperability complexity) and R12 (residual PHI at the vendor) are the two risks this doc carries; R33 (media in the tenant store) attaches to I7 now that ADR 015 fixed *where* objects live.
- Decisions needed: AI vendor **agreement** (U14 — the vendor is DeepSeek); the telehealth **vendor** (U29); the licensed **drug-data source** (U30); the **object-storage service** (U33); whether the first FHIR import targets one specific vendor or a generic FHIR endpoint (P2/P3).
- **Decided since the first draft (2026-09-24/25), so no longer "decisions needed":** the telehealth **mechanism** (ADR 009 — managed vendor behind an adapter), the pharmacy posture (partner-only, I5), the prescribing surface (ADR 010), the recording/retention policy (U31 → ADR 015) and the drug-data **rule** (ADR 017 — never a general model).

## Next action

Create the vendor mirrors + `MANIFEST.txt` entries **when each vendor is selected** (U14 agreement, U29, U30, U33 — each Deferred against a staged milestone, so none blocks the demo); the AI provider's **contract** and residency terms are the pilot gate, not the demo. This doc needs no further P-phase revision until a vendor is chosen — the integration *postures* now live in the ADRs (005/009/010/015/017).
