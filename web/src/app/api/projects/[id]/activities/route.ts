import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(req.url);
  return proxyToApi(`/v1/projects/${id}/activities${url.search}`, { method: "GET" });
}

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/projects/${id}/activities`, { method: "POST", body });
}
