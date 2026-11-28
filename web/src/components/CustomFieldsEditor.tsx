"use client";

type Props = {
  value: Record<string, string>;
  onChange: (next: Record<string, string>) => void;
};

export function CustomFieldsEditor({ value, onChange }: Props) {
  const rows = Object.entries(value);

  function setRow(index: number, key: string, fieldValue: string) {
    const next = [...rows];
    next[index] = [key, fieldValue];
    onChange(Object.fromEntries(next.filter(([k]) => k.trim())));
  }

  function remove(index: number) {
    const next = rows.filter((_, i) => i !== index);
    onChange(Object.fromEntries(next));
  }

  return (
    <div className="stack" style={{ gap: "0.4rem" }}>
      <span className="label">Custom fields</span>
      {rows.map(([key, fieldValue], index) => (
        <div key={index} style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: "0.4rem" }}>
          <input
            className="input"
            value={key}
            placeholder="contract_type"
            onChange={(e) => setRow(index, e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""), fieldValue)}
          />
          <input
            className="input"
            value={fieldValue}
            placeholder="Value"
            onChange={(e) => setRow(index, key, e.target.value)}
          />
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => remove(index)}>
            Remove
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => onChange({ ...value, [`field_${rows.length + 1}`]: "" })}
      >
        Add field
      </button>
    </div>
  );
}
