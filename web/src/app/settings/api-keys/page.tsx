import { redirect } from "next/navigation";
import { apiServerFetch, fetchMe } from "@/shared/server/session";
import { ApiKeysPanel } from "./ApiKeysPanel";

type KeyRow = {
  id: string;
  user_id: string;
  key_prefix: string;
  label: string | null;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
};

export default async function ApiKeysPage() {
  const me = await fetchMe();
  if (!me) redirect("/login");

  const res = await apiServerFetch("/v1/me/keys", { method: "GET" });
  const data = res.ok ? ((await res.json()) as { items: KeyRow[] }) : { items: [] };

  return (
    <div className="page-inner">
      <h1>API Keys</h1>
      <p className="text-sm muted">
        Personal API keys let coding agents (opencode, Claude Code, Cursor) query
        your project context through the MCP server. Keys are shown once on
        creation — copy and store them securely.
      </p>
      <ApiKeysPanel initialKeys={data.items} />
    </div>
  );
}
