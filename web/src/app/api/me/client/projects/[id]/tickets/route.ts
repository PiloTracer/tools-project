import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(req.url);
  return proxyToApi(`/v1/me/client/projects/${id}/tickets${url.search}`, { method: "GET" });
}
