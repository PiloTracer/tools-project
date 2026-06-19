## UIS-08 Intuitive UX

- **Discoverability:** ok — all primary actions visible (New prospect/client buttons, edit/delete in dropdowns/buttons, stage advance in menus). Filters, search, export all findable. Disabled states (terminal stages) show tooltip.
- **Feedback:** ok — skeleton loading on all screens, toast on create/edit/delete/advance, inline error banners with retry, form validation errors inline. No silent failures.
- **Error handling:** ok — delete guarded by confirmation dialog on all screens. Required field validation on forms. Terminal stage advance disabled with tooltip. Error messages in plain language. Stage transitions could show loading indicator but refetch is fast.
- **Cognitive load:** ok — prospects detail uses single-scroll layout with clear hierarchy (header → metrics → notes → pipeline progress). Clients detail splits into tabs (details/contacts). Filter bar separated from table. Empty states show text message but lack illustration/guide as described in SPEC §3 (minor).
- **Consistency:** ok — all CRM pages use same patterns: page-header pill+title+lead, DataTable, Dialog, DropdownMenu, Toast. Escape closes all dialogs. Back links consistent. Button classes consistent.
- **Overall:** ship — no blocking UX gaps. Minor polish: add illustrations to empty states, add loading spinner during stage transitions.
