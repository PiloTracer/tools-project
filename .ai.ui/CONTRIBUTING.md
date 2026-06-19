# Contributing to UI Design OS

1. **Never** add skills without the `ui-` prefix.
2. **Never** duplicate Agent OS skill ids or MOD concept ids in this repo.
3. Update [`skills/SKILL_DEPENDENCIES.md`](skills/SKILL_DEPENDENCIES.md) when adding gates.
4. Update [`COHABITATION.md`](COHABITATION.md) when a skill touches `.work/` or `.cursorrules`.
5. Run `bash scripts/framework-verify.sh` before opening a PR (derives skill count, cross-checks registration, prose counts, intake contract, and self-tests `readiness-verify` + `traceability-verify`).

Skill shape: `skill.md` with YAML frontmatter (`name` matches folder), modes table, hard rules, completion checklist.

**Cutting a release (maintainers):** `bash scripts/release.sh <version>` — refuses to create the annotated tag `v<version>` unless all verifiers pass, `CHANGELOG.md` has a matching `## [<version>]` section, and the tree is clean. It never pushes; review, then `git push origin main --follow-tags`.

Standards: `YYYYMMDD-*.md` templates with `REPLACE:UI_*` tokens only.
