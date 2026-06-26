import { proxyToApi } from "@/shared/server/proxy-api";

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ id: string; linkId: string }> },
) {
  const { id, linkId } = await params;
  return proxyToApi(`/v1/projects/${id}/github/links/${linkId}/sync`, {
    method: "POST",
  });
}
