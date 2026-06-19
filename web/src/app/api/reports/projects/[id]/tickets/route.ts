import { proxyBinaryFromApi } from "@/shared/server/proxy-api";

export async function GET(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const url = new URL(req.url);
  const qs = url.searchParams.toString();
  return proxyBinaryFromApi(`/v1/reports/projects/${id}/tickets${qs ? `?${qs}` : ""}`);
}
