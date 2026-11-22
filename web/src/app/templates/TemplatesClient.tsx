"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { sortTemplates, templatePresentation, type TemplateChoice } from "@/components/TemplatePicker";

export function TemplatesClient({
  templates,
  canAdd,
}: {
  templates: (TemplateChoice & { id: string })[];
  canAdd: boolean;
}) {
  const router = useRouter();
  const [team, setTeam] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [columns, setColumns] = useState("Requested\nDone *");
  const [types, setTypes] = useState("* Booking\nSetup");
  const [items, setItems] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ordered = sortTemplates(templates);
  const counts = new Map<string, number>();
  for (const template of ordered) {
    const teamName = template.team ?? "Basic";
    counts.set(teamName, (counts.get(teamName) ?? 0) + 1);
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const columnRows = columns
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const finished = line.endsWith("*");
        return { label: line.replace(/\*$/, "").trim(), is_finished: finished };
      });
    const typeRows = types
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const isDefault = line.startsWith("*");
        return { name: line.replace(/^\*/, "").trim(), is_default: isDefault };
      });
    const itemRows = items
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [title, columnLabel, workTypeName] = line.split("|").map((part) => part.trim());
        return { title, column_label: columnLabel, work_type_name: workTypeName };
      });
    const response = await fetch("/api/project-templates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        team: team.trim(),
        name: name.trim(),
        description: description.trim() || null,
        columns: columnRows,
        work_types: typeRows,
        items: itemRows.filter((row) => row.title && row.column_label && row.work_type_name),
      }),
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      setError(typeof body.detail === "string" ? body.detail : "Could not save. Try again.");
      setBusy(false);
      return;
    }
    setTeam("");
    setName("");
    setDescription("");
    setItems("");
    setBusy(false);
    router.refresh();
  }

  return (
    <div className="stack-lg">
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "0.65rem",
        }}
      >
        {ordered.map((template) => {
          const teamName = template.team ?? "Basic";
          const { title, subtitle } = templatePresentation(template, counts.get(teamName) ?? 1);
          return (
            <article key={template.id} className="card" style={{ padding: "0.8rem 0.9rem" }}>
              <strong style={{ fontSize: "1.05rem" }}>{title}</strong>
              {subtitle ? <div className="muted text-sm">{subtitle}</div> : null}
              {template.description ? (
                <p className="muted text-sm" style={{ margin: "0.35rem 0 0" }}>{template.description}</p>
              ) : null}
              <p className="muted text-sm" style={{ margin: "0.45rem 0 0" }}>
                {template.columns.length > 0
                  ? template.columns.map((column) => column.label).join(" → ")
                  : "Todo → In progress → Blocked → Done"}
              </p>
            </article>
          );
        })}
      </div>
      {canAdd ? (
        <form className="card stack" onSubmit={onSubmit}>
          <h2 style={{ marginTop: 0 }}>Add a template</h2>
          {error ? <p className="err" role="alert">{error}</p> : null}
          <label className="field">
            <span className="label">Team</span>
            <input className="input" required value={team} onChange={(event) => setTeam(event.target.value)} />
          </label>
          <label className="field">
            <span className="label">Name</span>
            <input className="input" required value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label className="field">
            <span className="label">Description</span>
            <textarea className="input" rows={2} value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label className="field">
            <span className="label">Columns — one per line. End a finished column with an asterisk.</span>
            <textarea className="input" rows={4} required value={columns} onChange={(event) => setColumns(event.target.value)} />
          </label>
          <label className="field">
            <span className="label">Item types — one per line. Mark the default with a leading asterisk.</span>
            <textarea className="input" rows={3} required value={types} onChange={(event) => setTypes(event.target.value)} />
          </label>
          <label className="field">
            <span className="label">Starter items — one per line, as title, then a vertical bar, then the column name, then a vertical bar, then the item type.</span>
            <textarea className="input" rows={3} value={items} onChange={(event) => setItems(event.target.value)} placeholder="Book the room | Requested | Booking" />
          </label>
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Saving…" : "Add template"}
          </button>
        </form>
      ) : (
        <p className="muted">Only an administrator can add a template.</p>
      )}
    </div>
  );
}
