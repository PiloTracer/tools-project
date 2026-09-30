export type MeResponse = {
  id: string;
  email: string;
  display_name: string | null;
  is_superuser: boolean;
  auth: string;
  client_contact_id: string | null;
  client_name: string | null;
  /** Multi-tenancy: populated only when MULTI_TENANCY_ENABLED is true. */
  tenant_id?: string | null;
  tenant_slug?: string | null;
  tenant_name?: string | null;
};
