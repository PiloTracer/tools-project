# Integration mirror (project-owned)

**Purpose:** Offline copies of vendor specs (OpenAPI, XSD, PDF, HTML) so agents and humans cite **files in the repo**, not memory or live URLs.

Agent OS ships **no vendor artifacts** in `.ai/` — each adopting project adds its own mirror here (or under a path declared in `.cursorrules`).

---

## Bootstrap

1. Create this directory in the **application repo** (often `.ai/docs/integration/` when `.ai/` is copied in).
2. Add a `MANIFEST.txt` — one line per artifact: `canonical_url<TAB>relative_path`.
3. Record `download_batch_date=` and any audit notes at the top of the manifest.
4. Reference the manifest from foundation doc 02, SPECs, and `@plan-master` / `@db-migration` when integration work is in scope.

**Template:** [`MANIFEST.template.txt`](MANIFEST.template.txt)

---

## Rules

- **Do not invent** endpoints, field names, or error codes — quote from mirrored files or mark **Unverified**.
- **Protected:** integration mirrors are usually **tracked**; do not delete vendor files without explicit owner permission (see `.cursorrules` § Protected Files).
- **Secrets:** never commit credentials, signing keys, or production tokens — only public vendor documentation.

---

## Skills that use this folder

| Skill | When |
|-------|------|
| `@plan-foundation` | Doc 02 — integration sources and evidence |
| `@plan-master` | Milestones touching external APIs |
| `@feature-spec` | SPEC § APIs / external contracts |
| `@code-implementation` | Tasks that call or parse vendor formats |

If your project has no external integrations yet, leave this folder empty except `README.md` and an empty or commented `MANIFEST.txt`.
