/** Shared CRM org/contact profile fields for prospects and clients. */

export type CrmOrgProfile = {
  org_email?: string | null;
  org_phone?: string | null;
  email?: string | null;
  phone?: string | null;
  working_schedule?: string | null;
  message?: string | null;
  service?: string | null;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

export type CrmContactProfile = {
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
};

export type CrmProfileFormState = {
  contactName: string;
  contactEmail: string;
  contactPhone: string;
  orgEmail: string;
  orgPhone: string;
  workingSchedule: string;
  message: string;
  service: string;
  address: string;
  latitude: string;
  longitude: string;
};

export const emptyCrmProfileForm = (): CrmProfileFormState => ({
  contactName: "",
  contactEmail: "",
  contactPhone: "",
  orgEmail: "",
  orgPhone: "",
  workingSchedule: "",
  message: "",
  service: "",
  address: "",
  latitude: "",
  longitude: "",
});

export function crmProfileFromProspect(row: CrmOrgProfile & CrmContactProfile): CrmProfileFormState {
  return {
    contactName: row.contact_name ?? "",
    contactEmail: row.contact_email ?? "",
    contactPhone: row.contact_phone ?? "",
    orgEmail: row.org_email ?? "",
    orgPhone: row.org_phone ?? "",
    workingSchedule: row.working_schedule ?? "",
    message: row.message ?? "",
    service: row.service ?? "",
    address: row.address ?? "",
    latitude: row.latitude != null ? String(row.latitude) : "",
    longitude: row.longitude != null ? String(row.longitude) : "",
  };
}

export function crmProfileFromClient(row: CrmOrgProfile): CrmProfileFormState {
  return {
    contactName: "",
    contactEmail: "",
    contactPhone: "",
    orgEmail: row.email ?? "",
    orgPhone: row.phone ?? "",
    workingSchedule: row.working_schedule ?? "",
    message: row.message ?? "",
    service: row.service ?? "",
    address: row.address ?? "",
    latitude: row.latitude != null ? String(row.latitude) : "",
    longitude: row.longitude != null ? String(row.longitude) : "",
  };
}

function opt(s: string): string | null {
  const t = s.trim();
  return t || null;
}

function optCoord(s: string): number | null {
  const t = s.trim();
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

/** Body keys for prospect create/patch. */
export function prospectProfileBody(form: CrmProfileFormState): Record<string, unknown> {
  return {
    contact_name: opt(form.contactName),
    contact_email: opt(form.contactEmail),
    contact_phone: opt(form.contactPhone),
    org_email: opt(form.orgEmail),
    org_phone: opt(form.orgPhone),
    working_schedule: opt(form.workingSchedule),
    message: opt(form.message),
    service: opt(form.service),
    address: opt(form.address),
    latitude: optCoord(form.latitude),
    longitude: optCoord(form.longitude),
  };
}

/** Body keys for client create/patch. */
export function clientProfileBody(form: CrmProfileFormState): Record<string, unknown> {
  return {
    email: opt(form.orgEmail),
    phone: opt(form.orgPhone),
    working_schedule: opt(form.workingSchedule),
    message: opt(form.message),
    service: opt(form.service),
    address: opt(form.address),
    latitude: optCoord(form.latitude),
    longitude: optCoord(form.longitude),
  };
}
