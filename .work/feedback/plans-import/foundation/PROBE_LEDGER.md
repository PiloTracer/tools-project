# Mendarion — probe ledger

**Scope:** foundation · **Updated:** 2026-09-25 · **Iterations:** 9 · **Coverage:** 90% (target 85%) — target **met**; no gate-blocking dimension below partial

> Persisted state for `@plan-foundation probe` / `@plan-master probe`. Engine: `.ai/skills/probe-protocol.md`.
> Set **confirmed/high** only with a cited source or a same-session owner answer; an inference is **partial/med** at best.
> Coverage = ( Σ weight × confidence ) / Σ weight · confidence high=1.0 med=0.5 low=0.0 · weight gate-blocking(★)=2 else=1.
> Evidence base: concept **revision 2** (`.work/prompts/Meridian — Practice Intelligence & Patient Connection OS (1).html`, cited as `concept §N`; revision 1 is history) + the covering note `.work/prompts/telehealth - ammendment.md`, the owner's 2026-09-24/25 answers (doc 01 §Revision 2, `.work/plans/proposals/20260924-consumer-platform-steer.md` §8, the P2 grill), and `doc 01`/`doc 04` rev 2.

## Coverage

| Dim | Topic | Status | Conf | Evidence / source | Iter |
|-----|-------|--------|------|-------------------|------|
| D1 ★ | Product intent & success | confirmed | high | Segment set + intent recorded verbatim (steer + owner answers 2026-09-24 → doc 01 §Revision 2, `.work/plans/proposals/20260924-consumer-platform-steer.md` §8); success criteria complete: S1–S3 (doc 01 §Success criteria v1) **plus S4 consumer onboarding ≤10 min, S5 routing ≥90% + zero missed red-flags, S6 zero missed high-severity safety hits** — proposed as assumed and **accepted by the owner** (§Success criteria, revision 2 additions) | 8 |
| D2 | Audience / personas | confirmed | high | `20260924-personas-v1.md` **revision 2** carries six demo audiences (incl. the **prospective consumer**) + P4–P10 (hospital admin, front desk, caregiver, pharmacist, platform owner, support) and journeys J1–J7 with budgets; the patient row now describes a **real account** (ADR 012), and the public surface has its own "what easy means" contract | 9 |
| D3 ★ | Scope in / out | confirmed | high | Demo in/out explicit (capability map + U28 demo acceptance); **staged order decided by the owner 2026-09-24**: AI routing + medication-safety alerts first, then practice self-service, then live telehealth, then pharmacy (doc 01 §Capability map); hospital-tier onboarding unsequenced; rev-1 never-list still in force | 8 |
| D4 | Functional capabilities | confirmed | high | Eleven capabilities with demo/staged labels (doc 01 §Capability map) mapped to **BC1–BC13** (doc 04 §3, phase-labelled) and to real packages in `20260924-DIRECTORY_MAP.md` §2 (incl. `consumer_record`, `directory`, `sharing`, `live`, `safety`, `prescribing` named now, empty until their milestone) | 9 |
| D5 ★ | NFRs | confirmed | high | Practice-side set accepted 2026-09-24 **plus** the revision-2 additions the owner accepted (video 720p / drop below ~1 Mbps / one-way latency <300 ms, enterprise tier 99.9%, directory p95 <300 ms, revocation ≤5 s, signup p95 <2 s) — all now **operative in doc 04 §5** with observable SLIs (`20260924-observability-spec.md` §6) | 9 |
| D6 | Integrations & ext deps | partial | med | Inventory **I1–I10** (doc 02: FHIR designed-not-built, CSV, AI, e-prescribing V3, pharmacy partner-only, SSO V3, **I7 telehealth vendor, I8 licensed drug-data source, I9 dial-in, I10 transcription**); AI vendor chosen (**DeepSeek**) with the agreement open (U14); each new integration's posture is now **decided in an ADR** (009/015/017) but the **vendor/licence selections remain open**: U29 (telehealth), U30 (drug data), U33 (object storage), U32 (Compass data); no mirrored vendor artifacts (MANIFEST empty) | 9 |
| D7 | Data model & sensitivity | confirmed | high | doc 04 §6 carries the revision entities (master file, grants, directory, occupation/job-safety, consultation/recording, prescriptions, Sentinel alerts, drug-data snapshots); `20260924-data-classification.md` §3 now tags **all three stores** (tenant / patient plane / platform index) with the **build-failing** rule for an unclassified public-index field; plane placement decided (ADR 011, U34) | 9 |
| D8 | Constraints | confirmed | high | **Team = 1 developer**, **demo deadline 2 weeks** (D-S3 kept it as milestone 1), budget not a tracked constraint, ops owner-managed — operator answers recorded in doc 01 §Constraints and A12/A23 | 5 |
| D9 ★ | Deploy / hosting / tenancy | partial | med | Stack + deploy path real and validated (`bin/start.sh`, `docker-compose.dev/prd.yml`, both `config` runs pass — ADR 008); hosting shape ADR 004; **tenancy is now decided**: ADR 002 + **ADR 011** (practice + enterprise tiers, `tier` attribute, the **dedicated patient-plane store**), ADR **012** supersedes 006's patient access, and the directory/grant topology is decided (013/014). Still **partial** because nothing is deployed **and the revision changes the deployment shape**: a second database class + object storage must be added to the stack (P5), region/residency stays U13, and images still cannot build until the app skeleton exists (R21/R23) | 9 |
| D10 ★ | Risks & assumptions | confirmed | high | Twenty-eight risks with mitigation + owner (R1–R28, incl. the revision's R24 patient-facing AI routing, R25 virtual pharmacy, R26 medication-safety alerting, R27 consumer identity + cross-practice sharing, R28 multi-segment scope — all H/H Open with mitigations); assumptions A1–A30 labeled, A4 rejected | 8 |

Status: `confirmed` | `partial` | `unknown` · Conf: `high` | `med` | `low` · ★ = gate-blocking.

## Open probes (carried to next iteration)

**No owner question remains open from the foundation.** Every gap recorded at iteration 8 was closed by artifact work in P1/P2/P3 on 2026-09-24/25:

- **D4 → closed:** doc 04 §3 carries **BC1–BC13** (phase-labelled) and `20260924-DIRECTORY_MAP.md` §2 names the matching packages.
- **D7 → closed:** doc 04 §6 carries the revision entities; `20260924-data-classification.md` §3 tags all three stores, with a build-failing rule for the public index.
- **D2 → closed:** `personas-v1.md` revision 2 (six demo audiences, J1–J7) supersedes the magic-link patient row.
- **D9 → closed at the decision level:** ADRs **011** (tiers + patient plane), **012** (identity) and 013/014 (directory, grants) are **Decided**; the *deployment* half (a second database class + object storage in the stack) is now an **explicit P5/implementation task**, which is why the dimension stays `partial/med`.
- **D6 → still partial, with owners:** the integration *postures* are decided (ADR 009/015/017), but **U29** (telehealth vendor + BAA), **U30** (licensed drug-data source), **U32** (Compass data) and **U33** (object-storage service) remain open — each is Deferred against a **staged** milestone, so none blocks the demo.
- **D5 → closed:** the revision-2 NFRs are operative in doc 04 §5 and have observable SLIs (observability spec §6).

**Re-run `@plan-foundation probe` if the demo scope changes** — the residual 10% is vendor/licence selection against staged milestones plus the un-deployed P5 shape, not missing understanding.

**p0-probe exit (iteration 8):** criteria met — D1 and D3 are **confirmed/high** (target: at least partial), D2 and D4 are addressed at partial, and every remaining gap is either deferred with an owner or scheduled into P1/P2.
**p2/p3/p6 exit (iteration 9, 2026-09-25):** the revision's artifact gaps are closed — D2/D4/D5/D7/D9-decision at **confirmed/high**, D6 and D9-deployment at partial with named owners; **coverage 90%** (target 85% **met**); `plan-master integrity` on the foundation artifacts → **pass**; **plan-master-ready re-certified**.
**GATE p0 (revision 2):** artifacts present (doc 01 rev 2, `.cursorrules`, the three registries) and the probe exit above is satisfied; shared gate integrity applied — registries reviewed, no unresolved contradictions found between doc 01 rev 2, doc 04 and the ADRs (the rev-2 supersessions are recorded, not silent).

## Deferred (→ UNKNOWNS.md)

- U6: which side the first milestone after the demo optimises (the 2026-09-24 ordering fixed *routing + safety alerts first*, which leans consumer/patient) · owner=operator · blocks=UX priority
- U9, U11, U16, U17, U20: **closed** (budget/ops, scheduling out of the slice, demo deliverable, slice confirmation, placeholder propagation)
- U12: business model (seat pricing, benchmarking revenue, **and now consumer/provider revenue**) · owner=operator · blocks=platform billing (P2)
- U13: primary jurisdiction + data-residency placement — now **doubly** blocking (PHI residency *and* telehealth licensure, *and* the AI vendor's residency posture) · owner=operator · blocks=`p2-hosting`, compliance ADR, telehealth
- U14: AI vendor agreement (BAA/DPA) + redaction evidence — **vendor chosen (DeepSeek)**, agreement open · owner=operator · blocks=assist against real patient data, R12
- U15: AI clinical-claims posture — wording sign-off + evaluation gate; now also covers the **routing wording** · owner=internal CTO collaborator · blocks=AI SPECs, R11/R14/R24
- U21–U28 (revision-2 unknowns): **all closed** — U21/U22/U23/U26/U28 by the owner's 2026-09-24 grill answers, U24 shape + mechanism (ADR 009), U25 (partner-only), U27 (assurance levels); **U31** closed (recording policy) and **U34** closed 2026-09-25 (dedicated consumer store). Still open and owned: **U29** (telehealth vendor), **U30** (licensed drug-data source), **U32** (Compass data deps), **U33** (object-storage service)

## Iteration log

| Iter | Date | Coverage | Dimensions touched | Notes |
|------|------|----------|--------------------|-------|
| 1–7 | 2026-09-24 | 50%→93% | D1–D10 | Practice-side foundation, P0→P6, certified plan-master-ready (details in the P6 rows of `HANDOFF.md`) |
| 8 | 2026-09-24 | **93% → 60% → 80%** | D1–D10 | **Probe re-run for the consumer re-baseline.** Re-scored honestly against the revised intent: the revision reopened D1 (criteria were practice-side), D3 (staged boundary), D5 (no NFRs for the new surfaces) and D9 (tenancy under revision), and dropped inference-heavy rows from partial/high to partial/med → **60%**. One batch of three questions (≤5 per protocol, all owner-answerable) closed the gate-blocking gaps: **D5** NFR additions accepted (video 720p/degradation/<300 ms latency, enterprise 99.9%, directory p95 <300 ms, revocation ≤5 s, signup p95 <2 s), **D1** S4–S6 accepted (onboarding ≤10 min unaided; routing ≥90% + zero missed red-flags; zero missed high-severity safety hits), **D3** post-demo order fixed (AI routing + medication-safety alerts → practice self-service → live telehealth → pharmacy) → **80%**. All three answers written to doc 01 §Revision 2. **P0 gate passes**; target 85% is not met by the five P1/P2 artifact gaps above, which is the honest state of a mid-revision foundation |
| 9 | 2026-09-25 | **80% → 90%** | D2, D4, D5, D6, D7, D9 | **Re-scored after P2/P3/P6.** The five gaps named at iteration 8 were closed by artifact work, so the affected rows rise to `confirmed/high`: **D2** (personas rev 2), **D4** (BC1–BC13 + named packages), **D5** (NFRs operative in doc 04 §5 with SLIs), **D7** (three stores tagged, build-failing index rule), **D9** at the decision level (ADRs 011/012/013/014 Decided). **D6** stays `partial/med` (four vendor/licence selections open, all Deferred against **staged** milestones) and **D9** stays `partial/med` on the deployment half (a second database class + object storage must enter the stack at P5) → **90%**, target **met**. **No owner question remains open from the foundation**; `plan-master integrity` → pass; **plan-master-ready re-certified** |
