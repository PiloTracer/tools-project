# ui-bootstrap — examples

## Adopt UI only (no Agent OS)

```text
@ui-bootstrap init create-cursorrules
```

Creates `.work.ui/` + full `.cursorrules` from `cursorrules.ui.template`.

## Adopt beside Agent OS

```text
@project-bootstrap init          # if .work/ and base .cursorrules missing
@ui-bootstrap init merge-cursorrules
```

## Check rules

```text
@ui-bootstrap status
bash .ai.ui/scripts/cursorrules-ui.sh status
```

## Unfilled tokens

```bash
rg 'REPLACE:UI_' .cursorrules
```

Fill with user in loop — do not invent stack paths.
