/** CRM form field visibility — local cache + server sync via /api/auth/me/preferences. */

export type CrmFormFieldKey =
  | "pipeline_stage"
  | "pipeline_value"
  | "source"
  | "industry"
  | "zone"
  | "contact_name"
  | "contact_email"
  | "contact_phone"
  | "org_email"
  | "org_phone"
  | "working_schedule"
  | "message"
  | "service"
  | "address"
  | "coordinates"
  | "notes";

export const CRM_FORM_FIELD_META: { key: CrmFormFieldKey; label: string; group: string }[] = [
  { key: "pipeline_stage", label: "Pipeline stage", group: "Pipeline" },
  { key: "pipeline_value", label: "Value (USD)", group: "Pipeline" },
  { key: "source", label: "Fuente", group: "Classification" },
  { key: "industry", label: "Giro de negocio", group: "Classification" },
  { key: "zone", label: "Zona", group: "Classification" },
  { key: "contact_name", label: "Contact name", group: "Contact" },
  { key: "contact_email", label: "Contact email", group: "Contact" },
  { key: "contact_phone", label: "Contact phone", group: "Contact" },
  { key: "org_email", label: "Organization email", group: "Organization" },
  { key: "org_phone", label: "Organization phone", group: "Organization" },
  { key: "service", label: "Service", group: "Organization" },
  { key: "working_schedule", label: "Working schedule", group: "Organization" },
  { key: "address", label: "Address", group: "Organization" },
  { key: "coordinates", label: "Coordinates", group: "Organization" },
  { key: "message", label: "Message", group: "Organization" },
  { key: "notes", label: "Notes", group: "Other" },
];

export const DEFAULT_CRM_FORM_FIELDS: Record<CrmFormFieldKey, boolean> = {
  pipeline_stage: true,
  pipeline_value: false,
  source: true,
  industry: true,
  zone: true,
  contact_name: true,
  contact_email: true,
  contact_phone: true,
  org_email: false,
  org_phone: false,
  working_schedule: false,
  message: false,
  service: false,
  address: false,
  coordinates: false,
  notes: false,
};

const STORAGE_KEY = "tpr.crm_form_fields.v1";

export function resolveCrmFormFields(
  raw: Partial<Record<CrmFormFieldKey, boolean>> | null | undefined
): Record<CrmFormFieldKey, boolean> {
  const out = { ...DEFAULT_CRM_FORM_FIELDS };
  if (!raw) return out;
  for (const key of Object.keys(DEFAULT_CRM_FORM_FIELDS) as CrmFormFieldKey[]) {
    if (typeof raw[key] === "boolean") out[key] = raw[key]!;
  }
  return out;
}

export function readCachedCrmFormFields(): Record<CrmFormFieldKey, boolean> {
  if (typeof window === "undefined") return { ...DEFAULT_CRM_FORM_FIELDS };
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_CRM_FORM_FIELDS };
    return resolveCrmFormFields(JSON.parse(raw) as Partial<Record<CrmFormFieldKey, boolean>>);
  } catch {
    return { ...DEFAULT_CRM_FORM_FIELDS };
  }
}

export function writeCachedCrmFormFields(fields: Record<CrmFormFieldKey, boolean>): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(fields));
  } catch {
    /* quota / private mode */
  }
}
