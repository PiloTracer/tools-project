"use client";

import { useMemo, useState } from "react";

export type TemplateChoice = {
  key: string;
  name: string;
  team: string | null;
  description: string | null;
  columns: { label: string }[];
};

const DEPARTMENT_ORDER = [
  "Engineering",
  "HR",
  "Design",
  "Legal",
  "Finance",
  "IT",
  "Project Management",
  "Sales",
  "Marketing",
  "Operations",
];

function departmentRank(team: string | null): number {
  if (!team) return -1;
  const index = DEPARTMENT_ORDER.indexOf(team);
  return index === -1 ? DEPARTMENT_ORDER.length : index;
}

export function templatePresentation(template: TemplateChoice, siblingCount: number): { title: string; subtitle: string | null } {
  const alone = template.key === "basic" || siblingCount <= 1;
  if (template.key === "basic") return { title: "Basic", subtitle: null };
  if (alone && template.team) return { title: template.team, subtitle: template.name };
  return { title: template.name, subtitle: template.team };
}

export function sortTemplates<T extends TemplateChoice>(templates: T[]): T[] {
  return [...templates].sort((a, b) => {
    if (a.key === "basic") return -1;
    if (b.key === "basic") return 1;
    const byTeam = departmentRank(a.team) - departmentRank(b.team);
    if (byTeam !== 0) return byTeam;
    return a.name.localeCompare(b.name);
  });
}

function matches(template: TemplateChoice, query: string): boolean {
  if (!query) return true;
  const haystack = [
    template.team,
    template.name,
    template.description,
    ...template.columns.map((column) => column.label),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

export function TemplatePicker({
  templates,
  value,
  onChange,
}: {
  templates: TemplateChoice[];
  value: string;
  onChange: (key: string) => void;
}) {
  const [query, setQuery] = useState("");
  const needle = query.trim().toLowerCase();
  const ordered = useMemo(() => sortTemplates(templates), [templates]);
  const visible = ordered.filter((template) => template.key === "basic" || matches(template, needle));
  const departments = visible.filter((template) => template.key !== "basic");
  const counts = new Map<string, number>();
  for (const template of departments) {
    const team = template.team ?? "Other";
    counts.set(team, (counts.get(team) ?? 0) + 1);
  }

  return (
    <fieldset className="stack" style={{ border: 0, padding: 0, margin: 0 }}>
      <legend className="label">Department</legend>
      <p className="muted text-sm" style={{ margin: "0.15rem 0 0.35rem" }}>
        Choose Finance, Marketing, or any other department. The project opens with that team&apos;s board.
        Basic keeps today&apos;s board.
      </p>
      <label className="field">
        <span className="label">Find a department</span>
        <input
          className="input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Finance, Marketing, Engineering…"
        />
      </label>
      <div
        role="radiogroup"
        aria-label="Department"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "0.65rem",
        }}
      >
        {visible.map((template) => {
          const team = template.team ?? "Other";
          const { title, subtitle } = templatePresentation(template, counts.get(team) ?? 1);
          const selected = value === template.key;
          return (
            <label
              key={template.key}
              className="card"
              style={{
                display: "block",
                padding: "0.8rem 0.9rem",
                cursor: "pointer",
                margin: 0,
                borderColor: selected ? "var(--accent)" : undefined,
                boxShadow: selected ? "inset 0 0 0 1px var(--accent)" : undefined,
                background: selected ? "color-mix(in srgb, var(--accent) 12%, transparent)" : undefined,
              }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                <input
                  type="radio"
                  name="template"
                  value={template.key}
                  checked={selected}
                  onChange={() => onChange(template.key)}
                  aria-checked={selected}
                />
                <strong style={{ fontSize: "1.05rem" }}>{title}</strong>
                {selected ? <span className="pill">Selected</span> : null}
              </span>
              {subtitle ? (
                <span className="muted text-sm" style={{ display: "block", marginTop: "0.2rem" }}>
                  {subtitle}
                </span>
              ) : null}
              {template.description ? (
                <span className="muted text-sm" style={{ display: "block", marginTop: "0.35rem" }}>
                  {template.description}
                </span>
              ) : null}
              {template.columns.length > 0 ? (
                <span className="muted text-sm" style={{ display: "block", marginTop: "0.45rem" }}>
                  {template.columns.map((column) => column.label).join(" → ")}
                </span>
              ) : (
                <span className="muted text-sm" style={{ display: "block", marginTop: "0.45rem" }}>
                  Todo → In progress → Blocked → Done
                </span>
              )}
            </label>
          );
        })}
      </div>
      {departments.length === 0 ? (
        <p className="muted text-sm">No department matches that. Clear the search to see Finance, Marketing, and the rest.</p>
      ) : null}
    </fieldset>
  );
}
