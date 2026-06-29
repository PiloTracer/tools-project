import { proxyToApi } from "@/shared/server/proxy-api";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string; projectId: string }> },
) {
  const { id, projectId } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/admin/users/${id}/project-membership/${projectId}`, { method: "PATCH", body });
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; projectId: string }> },
) {
  const { id, projectId } = await params;
  return proxyToApi(`/v1/admin/users/${id}/project-membership/${projectId}`, { method: "DELETE" });
}
