"use client";

import type { ReactNode } from "react";

import type { CrmFormFieldKey } from "@/shared/crm-form-prefs";
import type { CrmProfileFormState } from "@/shared/crm-profile";

type Props = {
  value: CrmProfileFormState;
  onChange: (next: CrmProfileFormState) => void;
  /** Prospects include primary contact fields; clients use Contacts separately. */
  showContact?: boolean;
  /** When false, the field is omitted from the form. Defaults to always visible. */
  isVisible?: (key: CrmFormFieldKey) => boolean;
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

export function CrmProfileFields({
  value,
  onChange,
  showContact = true,
  isVisible = () => true,
}: Props) {
  const set = <K extends keyof CrmProfileFormState>(key: K, v: CrmProfileFormState[K]) => {
    onChange({ ...value, [key]: v });
  };
  const show = isVisible;

  const showAnyContact =
    showContact &&
    (show("contact_name") || show("contact_email") || show("contact_phone"));
  const showClassification = show("industry") || show("zone");
  const showOrgBlock =
    show("org_email") ||
    show("org_phone") ||
    show("service") ||
    show("working_schedule") ||
    show("address") ||
    show("coordinates") ||
    show("message");

  return (
    <div className="stack" style={{ gap: "0.65rem" }}>
      {showClassification ? (
        <>
          <p className="muted text-sm" style={{ margin: 0 }}>
            Classification
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
            {show("industry") ? (
              <Field label="Giro de negocio">
                <input
                  className="input"
                  value={value.industry}
                  onChange={(e) => set("industry", e.target.value)}
                  placeholder="Retail, SaaS, Construction…"
                />
              </Field>
            ) : null}
            {show("zone") ? (
              <Field label="Zona">
                <input
                  className="input"
                  value={value.zone}
                  onChange={(e) => set("zone", e.target.value)}
                  placeholder="GAM, Norte, Pacific…"
                />
              </Field>
            ) : null}
          </div>
        </>
      ) : null}

      {showAnyContact ? (
        <>
          <p className="muted text-sm" style={{ margin: showClassification ? "0.35rem 0 0" : 0 }}>
            Primary contact
          </p>
          {show("contact_name") ? (
            <Field label="Contact name">
              <input
                className="input"
                value={value.contactName}
                onChange={(e) => set("contactName", e.target.value)}
                placeholder="Jane Doe"
              />
            </Field>
          ) : null}
          {show("contact_email") || show("contact_phone") ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
              {show("contact_email") ? (
                <Field label="Contact email">
                  <input
                    className="input"
                    type="email"
                    value={value.contactEmail}
                    onChange={(e) => set("contactEmail", e.target.value)}
                    placeholder="jane@acme.com"
                  />
                </Field>
              ) : null}
              {show("contact_phone") ? (
                <Field label="Contact phone">
                  <input
                    className="input"
                    value={value.contactPhone}
                    onChange={(e) => set("contactPhone", e.target.value)}
                    placeholder="+1 555 0100"
                  />
                </Field>
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}

      {showOrgBlock ? (
        <>
          <p
            className="muted text-sm"
            style={{ margin: showAnyContact || showClassification ? "0.35rem 0 0" : 0 }}
          >
            Organization
          </p>
          {show("org_email") || show("org_phone") ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.65rem" }}>
              {show("org_email") ? (
                <Field label="Organization email">
                  <input
                    className="input"
                    type="email"
                    value={value.orgEmail}
                    onChange={(e) => set("orgEmail", e.target.value)}
                    placeholder="hello@acme.com"
                  />
                </Field>
              ) : null}
              {show("org_phone") ? (
                <Field label="Organization phone">
                  <input
                    className="input"
                    value={value.orgPhone}
                    onChange={(e) => set("orgPhone", e.target.value)}
                    placeholder="+1 555 0101"
                  />
                </Field>
              ) : null}
            </div>
          ) : null}
          {show("service") ? (
            <Field label="Service">
              <input
                className="input"
                value={value.service}
                onChange={(e) => set("service", e.target.value)}
                placeholder="Consulting, implementation…"
              />
            </Field>
          ) : null}
          {show("working_schedule") ? (
            <Field label="Working schedule">
              <input
                className="input"
                value={value.workingSchedule}
                onChange={(e) => set("workingSchedule", e.target.value)}
                placeholder="Mon–Fri 9:00–17:00"
              />
            </Field>
          ) : null}
          {show("address") ? (
            <Field label="Address">
              <textarea
                className="input"
                rows={2}
                value={value.address}
                onChange={(e) => set("address", e.target.value)}
                placeholder="Street, city, country"
              />
            </Field>
          ) : null}
          {show("coordinates") ? (
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
          ) : null}
          {show("message") ? (
            <Field label="Message">
              <textarea
                className="input"
                rows={3}
                value={value.message}
                onChange={(e) => set("message", e.target.value)}
                placeholder="Inquiry or intake message"
              />
            </Field>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
