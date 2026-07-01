import { proxyToApi } from "@/shared/server/proxy-api";

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ keyId: string }> }
) {
  const { keyId } = await params;
  return proxyToApi(`/v1/me/keys/${encodeURIComponent(keyId)}`, {
    method: "DELETE",
  });
}
