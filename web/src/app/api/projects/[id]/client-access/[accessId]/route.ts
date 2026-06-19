import { proxyToApi } from "@/shared/server/proxy-api";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string; accessId: string }> },
) {
  const { id, accessId } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/projects/${id}/client-access/${accessId}`, { method: "PATCH", body });
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; accessId: string }> },
) {
  const { id, accessId } = await params;
  return proxyToApi(`/v1/projects/${id}/client-access/${accessId}`, { method: "DELETE" });
}
