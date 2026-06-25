import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return proxyToApi(`/v1/projects/${id}/github/readiness`, { method: "GET" });
}
