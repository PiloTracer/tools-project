# ui-screen-spec — invocation reference

Examples for `intake` and `create`. The skill's Modes table is canonical; this file shows good vs wrong prompts so the free-text front door routes predictably.

## intake — free-text front door

`@ui-screen-spec intake - <one plain-English sentence>`. Classifies by blast radius, routes to one command, records to `{UI_ITERATION_CARRIER}` § Intake queue. Only `local` proceeds into `create`.

### Good prompts

| Prompt | Likely class | Routes to |
|--------|--------------|-----------|
| `@ui-screen-spec intake - add a page to manage team members` | local | `create - team-members` |
| `@ui-screen-spec intake - we need a settings area with billing and profile tabs` | cross-cutting | `@ui-design-system init` → `plan` |
| `@ui-screen-spec intake - make the app feel more premium` | underspecified | `@ui-design-foundation probe` |
| `@ui-screen-spec intake - start the UI for our new invoicing product` | brownfield | `@ui-design-foundation greenfield` |
| `@ui-screen-spec intake - add a checkout page ; force=local` | local (forced) | `create - checkout` |

### Wrong prompts (and the fix)

| Wrong | Why | Do instead |
|-------|-----|------------|
| `@ui-screen-spec intake checkout` | Missing the `-` separator | `@ui-screen-spec intake - checkout page` |
| `@ui-screen-spec intake - <whole PRD pasted>` | Intake takes one sentence, not a document | One sentence → then `create`, attach detail in SPEC §1 |
| `@ui-screen-spec create - make it look nice` | `create` needs a slug or a screen-shaped sentence | `intake` first; it will classify as underspecified |
| Using `intake` to start a project with no foundation | Routes to brownfield anyway | `@ui-design-foundation greenfield` first |

## create — slug derivation

`@ui-screen-spec create - <slug | sentence>`.

| Arg | Behavior |
|-----|----------|
| `checkout` (kebab-case) | Use as-is |
| `team-settings-page` | Use as-is |
| `a page to manage team members` (sentence) | Propose derived slug `team-members`, state it, carry the sentence into SPEC §1 Summary |

Derivation: lowercase, drop filler words (a/the/page/screen/to/for), kebab-join the 1–3 salient nouns. Always state the proposed slug before writing; let the user override.

## See also

- Classification table + RECORD format: [`skill.md`](skill.md) § intake
- Pattern extraction (Phases A–C): [`examples/INDEX.md`](../../examples/INDEX.md) § playbook
- Standard: `standards/20260523-SCREEN_SPEC_STANDARD.md`
