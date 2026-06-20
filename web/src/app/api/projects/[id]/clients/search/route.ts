import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(req.url);
  const q = url.searchParams.get("q") || "";
  return proxyToApi(`/v1/projects/${id}/clients/search?q=${encodeURIComponent(q)}`, { method: "GET" });
}
