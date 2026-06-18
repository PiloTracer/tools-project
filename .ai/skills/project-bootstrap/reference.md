# project-bootstrap - reference

## Invocation examples

```
@project-bootstrap init
@project-bootstrap status
project-bootstrap work-only
```

## Adopting into an application repo

```text
my-app/
├── .ai/          ← copy Agent OS tree
├── .work/        ← bootstrap.sh creates skeleton
├── .cursorrules  ← from templates/cursorrules.template
└── DOCS_TECH_STACK.md
```

Run from `my-app/`:

```bash
bash .ai/templates/bootstrap.sh
```

## Framework-only repo (this tree is `.ai`)

When the git root **is** the Agent OS repository, `.work/` lives at the same root for demos and pointer link targets. Application code still lives in a separate app repo in production.

## After init

| Step | Skill |
|------|-------|
| Foundation | `@plan-foundation greenfield` |
| Certify | `@plan-foundation certify plan-master-ready` |
| Master plan | `@plan-master greenfield` |
| Daily | `@session-control start` |
