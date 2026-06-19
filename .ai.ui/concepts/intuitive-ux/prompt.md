# Intuitive UX — agent procedure (UIS-08)

## Inputs

- Screen SPEC §6 (interactions), §7 (states), §10 (edge cases)
- Component tree or rendered UI
- User goals / personas from foundation doc 01

## Procedure

1. **Discoverability & affordances** — Can users find every action without hunting? Do buttons look clickable, links look like links, disabled states read as disabled? Flag hidden gestures or features requiring prior knowledge.

2. **Feedback & responsiveness** — Does every user action produce immediate, clear feedback? Loading states, success confirmations, error messages that explain *why* and *what to do next*? No silent failures.

3. **Error prevention & forgiveness** — Are destructive actions reversible or guarded? Does the UI prevent common mistakes (disabled submit until valid, confirmation on delete, undo support)? Error messages plain language, not code or jargon.

4. **Cognitive load & progressive disclosure** — Are dense screens broken into steps or sections? Can a first-time user complete the primary task without reading instructions? Avoid blank-slate confusion — empty states should guide, not just say "nothing here."

5. **Consistency & predictability** — Do repeated patterns (dialogs, menus, inline edits) behave identically everywhere? Does back/escape navigation match user expectation? Surprises = bad.

## Output

```markdown
## UIS-08 Intuitive UX
- Discoverability: ok | weak — <what's hidden>
- Feedback: ok | missing | misleading — <examples>
- Error handling: ok | risky | unprotected — <destructive actions missing guards>
- Cognitive load: ok | heavy — <dense sections, empty-state gaps>
- Consistency: ok | drift — <inconsistent patterns>
- Overall: ship | revise — <top 1-2 fixes>
evidence: …
```
