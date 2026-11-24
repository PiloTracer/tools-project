"use client";

import type { ReactNode } from "react";

import type { CrmProfileFormState } from "@/shared/crm-profile";

type Props = {
  value: CrmProfileFormState;
  onChange: (next: CrmProfileFormState) => void;
  /** Prospects include primary contact fields; clients use Contacts separately. */
  showContact?: boolean;
};

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span className="label">{label}</span>
      {children}
    </label>
  );
}

export function CrmProfileFields({ value, onChange, showContact = true }: Props) {
  const set = <K extends keyof CrmProfileFormState>(key: K, v: CrmProfileFormState[K]) => {
    onChange({ ...value, [key]: v });
  };

  return (
    <div className="stack" style={{ gap: "0.65rem" }}>
      {showContact ? (
        <>
          <p className="muted text-sm" style={{ margin: 0 }}>
            Primary contact
          </p>
          <Field label="Contact name">
            <input
              className="input"
              value={value.contactName}
              onChange={(e) => set("contactName", e.target.value)}
              placeholder="Jane Doe"
            />
          </Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
            <Field label="Contact email">
              <input
                className="input"
                type="email"
                value={value.contactEmail}
                onChange={(e) => set("contactEmail", e.target.value)}
                placeholder="jane@acme.com"
              />
            </Field>
            <Field label="Contact phone">
              <input
                className="input"
                value={value.contactPhone}
                onChange={(e) => set("contactPhone", e.target.value)}
                placeholder="+1 555 0100"
              />
            </Field>
          </div>
        </>
      ) : null}

      <p className="muted text-sm" style={{ margin: showContact ? "0.35rem 0 0" : 0 }}>
        Organization
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
        <Field label="Organization email">
          <input
            className="input"
            type="email"
            value={value.orgEmail}
            onChange={(e) => set("orgEmail", e.target.value)}
            placeholder="hello@acme.com"
          />
        </Field>
        <Field label="Organization phone">
          <input
            className="input"
            value={value.orgPhone}
            onChange={(e) => set("orgPhone", e.target.value)}
            placeholder="+1 555 0101"
          />
        </Field>
      </div>
      <Field label="Service">
        <input
          className="input"
          value={value.service}
          onChange={(e) => set("service", e.target.value)}
          placeholder="Consulting, implementation…"
        />
      </Field>
      <Field label="Working schedule">
        <input
          className="input"
          value={value.workingSchedule}
          onChange={(e) => set("workingSchedule", e.target.value)}
          placeholder="Mon–Fri 9:00–17:00"
        />
      </Field>
      <Field label="Address">
        <textarea
          className="input"
          rows={2}
          value={value.address}
          onChange={(e) => set("address", e.target.value)}
          placeholder="Street, city, country"
        />
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
        <Field label="Latitude">
          <input
            className="input"
            inputMode="decimal"
            value={value.latitude}
            onChange={(e) => set("latitude", e.target.value)}
            placeholder="9.9281000"
          />
        </Field>
        <Field label="Longitude">
          <input
            className="input"
            inputMode="decimal"
            value={value.longitude}
            onChange={(e) => set("longitude", e.target.value)}
            placeholder="-84.0907000"
          />
        </Field>
      </div>
      <Field label="Message">
        <textarea
          className="input"
          rows={3}
          value={value.message}
          onChange={(e) => set("message", e.target.value)}
          placeholder="Inquiry or intake message"
        />
      </Field>
    </div>
  );
}
