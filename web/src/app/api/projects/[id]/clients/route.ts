import { proxyToApi } from "@/shared/server/proxy-api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  return proxyToApi(`/v1/projects/${id}/clients`, { method: "GET" });
}

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/projects/${id}/clients`, { method: "POST", body });
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const url = new URL(req.url);
  const clientId = url.searchParams.get("client_id");
  if (!clientId) {
    return new Response(JSON.stringify({ detail: "client_id query param required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
  return proxyToApi(`/v1/projects/${id}/clients/${clientId}`, { method: "DELETE" });
}
