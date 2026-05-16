import { proxyToApi } from "@/shared/server/proxy-api";

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string; userId: string }> },
) {
  const { id, userId } = await params;
  const body = await req.text();
  return proxyToApi(`/v1/projects/${id}/members/${userId}`, {
    method: "PATCH",
    body,
  });
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; userId: string }> },
) {
  const { id, userId } = await params;
  return proxyToApi(`/v1/projects/${id}/members/${userId}`, {
    method: "DELETE",
  });
}
