export type MeResponse = {
  id: string;
  email: string;
  display_name: string | null;
  is_superuser: boolean;
  auth: string;
};
