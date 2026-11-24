"use client";

import { useState } from "react";

import {
  CRM_FORM_FIELD_META,
  type CrmFormFieldKey,
} from "@/shared/crm-form-prefs";

type Props = {
  fields: Record<CrmFormFieldKey, boolean>;
  onToggle: (key: CrmFormFieldKey, visible: boolean) => void;
  /** Hide contact toggles on client forms (contacts are a separate section). */
  hideContact?: boolean;
  /** Hide pipeline toggles on client forms. */
  hidePipeline?: boolean;
};

export function CrmFormFieldsCustomize({
  fields,
  onToggle,
  hideContact = false,
  hidePipeline = false,
}: Props) {
  const [open, setOpen] = useState(false);

  const items = CRM_FORM_FIELD_META.filter((m) => {
    if (hideContact && m.group === "Contact") return false;
    if (hidePipeline && m.group === "Pipeline") return false;
    return true;
  });

  const groups = Array.from(new Set(items.map((i) => i.group)));

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-sm)",
        background: "var(--surface)",
        padding: "0.5rem 0.65rem",
      }}
    >
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        style={{
          width: "100%",
          justifyContent: "space-between",
          padding: "0.15rem 0",
          fontWeight: 500,
        }}
      >
        <span>Customize fields</span>
        <span className="muted text-sm">{open ? "Hide" : "Show / hide"}</span>
      </button>
      {open ? (
        <div style={{ marginTop: "0.5rem" }}>
          <p className="muted text-sm" style={{ margin: "0 0 0.5rem" }}>
            Choose which fields appear on create and edit. Saved for your account.
          </p>
          {groups.map((group) => (
            <div key={group} style={{ marginBottom: "0.5rem" }}>
              <div className="muted text-sm" style={{ fontWeight: 600, marginBottom: "0.25rem" }}>
                {group}
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "0.25rem 0.75rem",
                }}
              >
                {items
                  .filter((i) => i.group === group)
                  .map((item) => (
                    <label
                      key={item.key}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        fontSize: "0.82rem",
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={fields[item.key] !== false}
                        onChange={(e) => onToggle(item.key, e.target.checked)}
                      />
                      {item.label}
                    </label>
                  ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
