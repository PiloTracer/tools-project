import { proxyToApi } from "@/shared/server/proxy-api";

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; refId: string }> },
) {
  const { id, refId } = await params;
  return proxyToApi(`/v1/projects/${id}/github/refs/${refId}`, {
    method: "DELETE",
  });
}
