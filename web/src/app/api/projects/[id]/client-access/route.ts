import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return proxyToApi(`/v1/projects/${id}/client-access`, { method: "GET" });
}

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/projects/${id}/client-access`, { method: "POST", body });
}
