import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(_req.url);
  const qs = url.searchParams.toString();
  return proxyToApi(`/v1/admin/users/${id}/linkable-contacts${qs ? `?${qs}` : ""}`, { method: "GET" });
}
