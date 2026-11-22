# Project templates — Screen SPEC

**Status:** Approved
**Needs:** Build after the API from the feature SPEC exists. Button, input, and radio use the waivers in §8.
**Slug:** project-templates
**Path:** `.work.ui/screens/project-templates/20261122-SCREEN-SPEC.md`

The person picks a process, names the project, and lands on a task board whose columns are that process. A superuser can add another process. Rules for columns, item types, and starter items live only in `.work/features/project-templates/20261122-SPEC.md`.

## 1. Summary

**New project** (`/projects/new`) opens with **Basic** selected. The other cards are grouped by team. Each card shows the process name, one line of what it tracks, and its column names in order. Saving creates the project and opens its task board.

**Templates** (`/templates`) shows the same groups. A superuser gets a form to add a process. Everyone else sees the gallery and one sentence that only an administrator can add one.

The existing task board (`/projects/{id}/tasks`) reads that project's columns when they exist. A Basic project, and every project that already exists, keeps Todo, In Progress, Blocked, Done, and Cancelled.

## 2. Personas & jobs

| Persona | Job |
|---------|-----|
| Project owner or maintainer | Start a project that already follows a process, and move work across that process's columns |
| Superuser | Add a process the gallery does not have |
| Anyone else signed in | Read the gallery. The add form is absent. |

## 3. States

| State | Behaviour |
|-------|-----------|
| loading | Three skeleton cards in the picker. Save stays disabled until the gallery has loaded. |
| empty | The gallery always includes the shipped processes. A failed load is the error state. |
| error | One sentence in an alert. The name, slug, description, and selected card stay. |
| success | Create opens `/projects/{id}/tasks` on the board. Add-template clears the form and shows the new card in its team. |
| permission-denied | Non-superuser on `/templates` sees the gallery and "Only an administrator can add a template." |
| partial | List loaded, save failed. Same as error. |

## 4. Layout & hierarchy

The choice is the first thing on New project. Name, slug, and description stay under it in the current card width. Cards wrap: two columns from 720px, one column below.

| Region | Example id | Notes |
|--------|------------|-------|
| Team group | dashboards/D13 | A heading per team. Basic sits alone, above the teams, and starts selected. |
| Process card | dashboards/D7 | Name, one-line description, column names in order. |
| Project fields | dashboards/D7 | Name, slug, description, Create project. |
| Task board | dashboards/D7 | Existing board. Column headers come from the project when it has columns. |
| Add process | dashboards/D13 | Superuser only, under the gallery on `/templates`. |

No gradient hero, no second navigation, no chart, no calendar.

### Visual decision (required before Approved)

| Field | Value |
|-------|-------|
| Signature | The selected process card, with its column names readable before the project exists. |
| Type roles | Page title is the existing `h1`. Team name is a section heading. Card title is the process name. Column names and the description use the existing muted small text. |
| Density | product |
| Forbidden | Gradient hero, illustration, a fake miniature board, a chart, Atlassian colors or assets. |

## 5. Content

| Element | Copy |
|---------|------|
| Picker label | Template |
| Basic description | Today's project. The current board and the current work types. |
| Card columns | The column labels, in order, separated by arrows. |
| Selected | Selected |
| Save | Create project |
| Catalog title | Templates |
| Catalog lead | Choose a way of working for a new project. Projects you already have keep their board. |
| Add title | Add a template |
| Team field | Team |
| Columns field | Columns — one per line. End a finished column with an asterisk. |
| Types field | Item types — one per line. Mark the default with a leading asterisk. |
| Items field | Starter items — one per line, as title, then a vertical bar, then the column name. |
| Add save | Add template |
| Non-admin | Only an administrator can add a template. |
| Save failure | Could not save. Try again. |

## 6. Interactions

- The picker is one radio group labelled "Template". Cards follow team order from the API, Basic first.
- Basic is selected on first paint. A save before the user picks sends `template_key: "basic"`.
- After the list loads, the selection stays where the user put it.
- Focus order on New project: kit radios, name, slug, description, Create project.
- Focus order on the add form: team, name, description, columns, item types, starter items, Add template.
- No modal. Escape does nothing.
- On the task board, dragging a card to a column calls the existing status update with that column's key.

## 7. Data dependencies

- `.work/features/project-templates/20261122-SPEC.md`
- `GET /v1/project-templates`
- `POST /v1/projects` with `template_key`
- `POST /v1/project-templates`
- `GET /v1/projects/{id}/board-columns` for the task board and the task detail status control
- An empty column list means the five columns the board uses today
- Work-type marks stay on `WorkTypeBadge`. This screen prints type names as text.

## 8. Tokens & components

Classes already on the new-project page: `.page-inner`, `.card`, `.field`, `.label`, `.input`, `.btn`, `.btn-primary`, `.muted`, `.err`. No new tokens. No edit to `web/src/app/globals.css`.

| Component | Catalog status | Native waiver |
|-----------|----------------|---------------|
| Card surface | utility class `.card` | native allowed — existing page pattern |
| Button | `.btn`, `.btn-primary` — CATALOG.md has no Button primitive | native allowed |
| Text field and textarea | `.input` | native allowed |
| Radio cards | no Radio primitive | native allowed — `<input type="radio">` inside the card label |
| Skeleton | done — `web/src/components/Skeleton.tsx` | — |
| Task board | existing `KanbanBoard` | — column list becomes an argument when the project has columns |
| Alert | `.err` with `role="alert"` | native allowed |

## 9. Accessibility

WCAG AA. The radio group has a visible legend. The selected card shows the word "Selected" and a visible focus ring. The error is `role="alert"`. Skeleton cards are `aria-hidden`. Column names are text, so the process is understandable without color. No new animation.

## 10. Analytics

No new browser events. The server log `project.template_applied` carries the key and the project id only.

## 11. Acceptance criteria

- [ ] Cards on a light background, one primary save button, two columns from 720px and one column below.
- [ ] Basic is selected on open. Create project with no other choice sends `basic` and opens a board with Todo, In Progress, Blocked, Done, and Cancelled.
- [ ] Choosing Bug tracking and creating the project opens a board whose columns are Captured, Triaged, In progress, Verify, and Done, with the three starter items in the columns named in the feature SPEC.
- [ ] Choosing Recruitment, moving an item to Hired, and opening it shows that item finished. The status control lists the Recruitment columns.
- [ ] A project that already existed still shows the five current columns, and its items are unchanged.
- [ ] A non-superuser does not see the add form.
- [ ] A superuser can add a Facilities process with two columns, two item types, and one starter item, then create a project whose board is those two columns.
- [ ] A failed save leaves the name and the selected card in place.
- [ ] The radio group is reachable from the keyboard and the focus ring is visible.

## 12. Concept / UIS registry

| UIS | Applies | Reason | Status |
|-----|---------|--------|--------|
| UIS-01 | yes | Grouped card gallery and the existing board | pending |
| UIS-02 | yes | Team heading, process title, muted column line | pending |
| UIS-03 | no | No new tokens | N/A |
| UIS-04 | yes | Radio cards and the add form | pending |
| UIS-05 | yes | Focus order in §6 | pending |
| UIS-06 | yes | Agent-built screen | pending |
| UIS-07 | yes | Craft tier is refined | pending |
| UIS-08 | yes | Required before ship | pending |
| UIS-09 | no | No charts | N/A |
| UIS-10 | no | No marketing page | N/A |

## 13. Visual references

| Field | Value |
|-------|-------|
| **exampleIds** | `dashboards/D7`, `dashboards/D13` |
| **manifestPaths** | `/mnt/work/Projects/pilo.ai.ui.logicbison/examples/dashboards/manifest.md` |
| **craftTier** | refined |
| **beforeScreenshot** | none — today's new-project form and task board are the Basic layout |

### extractedRules (binding)

- Spacious product layout, primary button, cards on a light background. From D7.
- Grouped cards, two columns on desktop and one column on a narrow viewport. The add action is hidden for people who cannot use it. From D13.

### regionMap

| §4 region | example id |
|-----------|------------|
| Team group | dashboards/D13 |
| Process card | dashboards/D7 |
| Project fields | dashboards/D7 |
| Task board | dashboards/D7 |
| Add process | dashboards/D13 |

### Figma / external (optional)

- https://www.atlassian.com/software/jira/templates — the catalog of processes. Do not copy Atlassian layout, color, or assets.
- https://www.atlassian.com/software/jira/templates/recruitment — a process is a board whose columns are the steps.
- https://www.atlassian.com/software/jira/templates/bug-tracking — a process has its own steps, separate from a generic task list.

## Decisions needed

none — approved 2026-11-22 with the feature SPEC.

## Next action

`@ui-component-build plan` for this screen, after `@code-implementation plan - project-templates`.
