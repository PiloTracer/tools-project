import { proxyToApi } from "@/shared/server/proxy-api";

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; contactId: string }> },
) {
  const { id, contactId } = await params;
  return proxyToApi(`/v1/clients/${id}/contacts/${contactId}`, { method: "DELETE" });
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string; contactId: string }> },
) {
  const { id, contactId } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/clients/${id}/contacts/${contactId}`, { method: "PATCH", body });
}
