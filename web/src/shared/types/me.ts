export type MeResponse = {
  id: string;
  email: string;
  display_name: string | null;
  is_superuser: boolean;
  auth: string;
  client_contact_id: string | null;
  client_name: string | null;
};
